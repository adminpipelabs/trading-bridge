# Phase 2 Deployment Verification Checklist

## ✅ Pre-Deployment Status

**Completed Tasks:**
- ✅ Task 1: Database Backups
- ✅ Task 2: Circuit Breaker for Jupiter API
- ✅ Task 3: Retry Logic with Exponential Backoff
- ✅ Task 4: Frontend Error Boundaries
- ✅ Task 6: Migration Strategy (Alembic)

**Deferred:**
- ⏸️ Task 5: Bot Runner Separation (defer until stable)

## 🧪 Post-Deployment Verification

### 1. Health Endpoints

```bash
# Main health check
curl https://trading-bridge-production.up.railway.app/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "Trading Bridge",
#   "database": "postgresql",
#   "bot_runner": {
#     "status": "running",
#     "active_bots": 1
#   }
# }

# Bot runner specific health
curl https://trading-bridge-production.up.railway.app/health/bot-runner

# Expected response:
# {
#   "status": "healthy",
#   "running_bots": 1,
#   "bots": [...]
# }
```

### 2. Bot Trading Verification

**Check bot stats:**
- Bot status should be "running"
- `last_trade_at` should be recent (< 1 hour old)
- Check Solscan for recent trades on wallet `BPaJfwA4...`

**Check logs for:**
- No circuit breaker errors (unless Jupiter API is actually down)
- Retry attempts (should see exponential backoff if transient errors)
- Successful trades executing

### 3. Frontend Error Handling

**Test error boundaries:**
1. Navigate to Admin Dashboard
2. Check browser console for errors
3. Verify error boundaries catch component errors gracefully
4. Test "Try Again" button works

**Expected behavior:**
- Component errors don't crash entire app
- User-friendly error messages shown
- Retry functionality works

### 4. Railway Logs Review

**Check for:**
- ✅ No new errors introduced
- ✅ Structured JSON logging working
- ✅ Circuit breaker logging (if triggered)
- ✅ Retry attempts logged correctly
- ✅ Bot runner starting successfully

**Log patterns to watch:**
```json
// Good - Structured logging
{"timestamp": "...", "level": "info", "logger": "app.bot_runner", "message": "Trade successful", "bot_id": "..."}

// Good - Circuit breaker protecting
{"timestamp": "...", "level": "warning", "logger": "app.solana.jupiter_client", "message": "Jupiter price API error: 503", ...}

// Bad - Should investigate
{"timestamp": "...", "level": "error", ...}
```

### 5. API Functionality

**Test endpoints:**
```bash
# Bot list (should work)
curl -H "Authorization: Bearer $TOKEN" \
  https://trading-bridge-production.up.railway.app/bots

# Create bot (should work)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", ...}' \
  https://trading-bridge-production.up.railway.app/bots/create

# Start/stop bot (should work)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://trading-bridge-production.up.railway.app/bots/{id}/start
```

### 6. Circuit Breaker Behavior

**If Jupiter API is down:**
- Circuit breaker should open after 5 failures
- Subsequent calls should fail fast (no retries)
- Bot should skip trades gracefully
- Logs should show "Circuit breaker open" messages

**If Jupiter API recovers:**
- Circuit breaker should attempt recovery after 60 seconds
- If successful, normal operation resumes
- Logs should show recovery

### 7. Retry Logic Behavior

**On transient errors:**
- Should see retry attempts in logs
- Exponential backoff: 2s, 4s, 8s delays
- Maximum 3 attempts
- If all fail, exception raised

**Check logs for:**
```
INFO: Retrying in 2 seconds...
INFO: Retrying in 4 seconds...
INFO: Retrying in 8 seconds...
```

## 🚨 Rollback Plan

If issues are found:

1. **Circuit Breaker Issues:**
   - Remove `@circuit` decorators from `jupiter_client.py`
   - Remove `circuitbreaker` from requirements.txt
   - Redeploy

2. **Retry Logic Issues:**
   - Remove `@retry` decorators from `jupiter_client.py`
   - Remove `tenacity` from requirements.txt
   - Redeploy

3. **Frontend Issues:**
   - Revert ErrorBoundary changes
   - Redeploy frontend

4. **Full Rollback:**
   ```bash
   git revert HEAD~2  # Revert last 2 commits
   git push origin main
   ```

## ✅ Success Criteria

- [ ] Health endpoints return healthy status
- [ ] Bot continues trading normally
- [ ] No new errors in logs
- [ ] Frontend error boundaries working
- [ ] API endpoints functional
- [ ] Circuit breaker protecting (if API issues occur)
- [ ] Retry logic handling transient errors
- [ ] Structured logging working

## 📝 Notes

- **Current Scale:** System designed for <10 bots, <5 clients
- **Task 5 Deferred:** Bot runner separation can wait until:
  - Current changes verified stable
  - Scaling to 5+ clients
  - Quiet day for refactoring

## 🔍 Monitoring

**Watch for:**
- Circuit breaker opening frequently (indicates Jupiter API issues)
- Retry attempts increasing (indicates network instability)
- Bot trade frequency decreasing (indicates issues)
- Error rates increasing (indicates problems)

**Alert thresholds:**
- Circuit breaker open > 5 minutes
- Bot not trading > 2 hours
- Error rate > 10% of requests
