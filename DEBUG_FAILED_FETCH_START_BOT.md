# Debug: "Failed to fetch" when starting bot

## Issue
User gets "Failed to fetch" error when clicking "Start Bot"

## Possible Causes

### 1. Backend Not Running
- Check Railway logs to see if backend started successfully
- Check if `/health` endpoint responds

### 2. CORS Issue
- Browser blocking request before it reaches server
- Check browser console for CORS errors
- Verify CORS config in `main.py` includes `https://app.pipelabs.xyz`

### 3. Network Error
- Request timing out
- Backend taking too long to respond
- Check Railway logs for slow requests

## What We've Done

1. ✅ Fixed Request injection syntax error (parameter ordering)
2. ✅ Added detailed error logging in frontend
3. ✅ Added network error catching in `apiCall`

## Next Steps to Debug

1. **Check Browser Console (F12)**
   - Look for detailed error logs we added
   - Check Network tab for the actual request
   - See if request shows "Failed" or "CORS error"

2. **Check Railway Logs**
   - Is backend running?
   - Any errors when request arrives?
   - Check for `/bots/{id}/start` requests

3. **Test Backend Directly**
   ```bash
   curl -X POST "https://trading-bridge-production.up.railway.app/bots/{BOT_ID}/start" \
     -H "Content-Type: application/json" \
     -H "X-Wallet-Address: {WALLET_ADDRESS}"
   ```

## Expected Behavior After Fix

- Frontend should show detailed error in console
- Network errors will be caught and logged
- User will see more specific error message
