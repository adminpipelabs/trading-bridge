# Troubleshooting Bot Creation Error

## Error: Internal Server Error

**When:** Creating bot via `/bots/create` endpoint

**Possible Causes:**

### 1. **Hummingbot API Not Accessible**

**Check:**
- Are environment variables set in Railway?
- Is Hummingbot API reachable from Railway?

**Solution:**
- Verify `HUMMINGBOT_API_URL` is set correctly
- If using Tailscale, make sure Tailscale is running
- Test connection: `curl -u admin:admin http://<hummingbot-url>/bot-orchestration/status`

---

### 2. **Environment Variables Not Set**

**Check Railway:**
1. Go to Railway Dashboard
2. Trading Bridge service → Variables tab
3. Verify these are set:
   - `HUMMINGBOT_API_URL`
   - `HUMMINGBOT_API_USERNAME`
   - `HUMMINGBOT_API_PASSWORD`

**Solution:**
- Add missing variables
- Redeploy Trading Bridge

---

### 3. **Network Connection Issue**

**If using Tailscale:**
- Check Tailscale is running: `tailscale status`
- Verify IP is correct: `tailscale ip -4`
- Make sure Railway can reach your Tailscale IP

**If deploying to Railway:**
- Use internal service URL: `http://hummingbot-api:8000`
- Make sure both services are in same Railway project

---

### 4. **Script Generation Error**

**Check:**
- Strategy name matches supported strategies
- Config parameters are valid

**Supported strategies:**
- `market_making` or `spread`
- `volume`

**Solution:**
- Use correct strategy name
- Check config parameters match expected format

---

## Debug Steps

### Step 1: Check Railway Logs

Go to Railway Dashboard → Trading Bridge → Logs

Look for:
- Connection errors
- Authentication errors
- Script generation errors

### Step 2: Test Hummingbot API Directly

```bash
# Test from your local machine
curl -u admin:admin http://localhost:8000/bot-orchestration/status

# Should return: {"status":"success","data":{}}
```

### Step 3: Test Trading Bridge Endpoints

```bash
# Get bots (should work even if Hummingbot unavailable)
curl https://trading-bridge-production.up.railway.app/bots

# Check root endpoint
curl https://trading-bridge-production.up.railway.app/
```

### Step 4: Check Environment Variables

In Railway logs, look for:
- "HummingbotClient initialized: ..."
- Connection errors
- Authentication errors

---

## Common Errors

### Error: "Connection refused"
**Cause:** Hummingbot API not reachable  
**Solution:** Check network setup (Tailscale or Railway)

### Error: "Not authenticated"
**Cause:** Wrong credentials  
**Solution:** Verify username/password in Railway variables

### Error: "Script generation failed"
**Cause:** Invalid strategy or config  
**Solution:** Check strategy name and config parameters

### Error: "Bot already exists"
**Cause:** Bot name already in use  
**Solution:** Use different bot name

---

## Quick Fixes

### Fix 1: Verify Environment Variables

```bash
# In Railway, check variables are set:
HUMMINGBOT_API_URL=http://localhost:8000  # or Tailscale IP
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=admin
```

### Fix 2: Test Connection

```bash
# From Railway container (check logs) or locally:
curl -u admin:admin http://localhost:8000/bot-orchestration/status
```

### Fix 3: Check Railway Logs

Look for error messages that indicate:
- Connection failures
- Authentication failures
- Script generation errors

---

## Next Steps

1. **Check Railway logs** for specific error message
2. **Verify environment variables** are set
3. **Test Hummingbot API** directly
4. **Check network connectivity** (Tailscale or Railway)

---

**Share the Railway logs error message for more specific help!**
