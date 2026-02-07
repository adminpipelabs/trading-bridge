# Diagnostic: Start Bot Error

## Current Implementation Status

### ✅ Bot Status Display - CORRECT
The code is already using `status` field correctly:
```javascript
// Line 435-439 in ClientDashboard.jsx
bot?.status === 'running' ? '🟢 ON' :
bot?.status === 'stopped' ? '🔴 OFF' :
bot?.health_status === 'stale' ? '🟡 Stale' :  // Fallback
bot?.health_status === 'error' ? '⚠️ Error' :   // Fallback
'⚪ Unknown'
```

**Status:** ✅ Already correct - uses `status` for ON/OFF, `health_status` for health indicators

---

### ⚠️ Start Bot Endpoint - POTENTIAL ISSUE

**Current Backend Code (line 800):**
```python
http_request: Request = None
```

**Problem:** FastAPI won't inject `Request` object if it has a default value of `None`. This means `http_request` will always be `None`, causing:
- Line 810: `http_request.headers.get()` will fail
- Line 817: `http_request.headers.get()` will fail
- Authentication checks will fail

**Fix Needed:**
```python
# Change from:
http_request: Request = None

# To:
request: Request  # FastAPI will auto-inject
```

---

## What to Check First (Per Dev's Instructions)

### 1. Check Browser Console
Open browser console (F12) when clicking "Start Bot" and look for:
- CORS errors
- Network errors
- Actual HTTP status code
- Error message details

### 2. Check Network Tab
In browser DevTools → Network tab:
- Find the `POST /bots/{bot_id}/start` request
- Check:
  - Status code (401? 403? 500? CORS error?)
  - Request headers (is Authorization header sent?)
  - Response body (what error message?)

### 3. Check Railway Logs
Look for:
```
POST /bots/xxx/start
401/403/500 errors
Exception/traceback
```

---

## Recommended Fix (After Checking Logs)

If logs show authentication/Request issues, fix the Request injection:

**File:** `trading-bridge/app/bot_routes.py`
**Line:** 800

**Change:**
```python
# BEFORE:
async def start_bot(
    bot_id: str, 
    db: Session = Depends(get_db),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    http_request: Request = None  # ❌ Won't work
):

# AFTER:
async def start_bot(
    bot_id: str, 
    db: Session = Depends(get_db),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    request: Request  # ✅ FastAPI will auto-inject
):
```

Then update references:
- Line 810: `http_request.headers.get()` → `request.headers.get()`
- Line 817: `http_request.headers.get()` → `request.headers.get()`

---

## Next Steps

1. ✅ Bot status display - Already correct, no changes needed
2. ⏳ Check browser console/network tab for actual error
3. ⏳ Check Railway logs for backend errors
4. ⏳ Apply Request injection fix if needed

**Do NOT deploy until we see actual error from logs/console.**
