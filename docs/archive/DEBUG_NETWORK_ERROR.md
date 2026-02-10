# Debug: "Network error: Failed to fetch"

## Current Status

**Error:** "Failed to fetch" when clicking "Start Bot"

**Backend Status:** ✅ Backend is reachable (curl test shows 404, which is expected for test bot)

**Likely Cause:** CORS blocking the request OR browser security blocking it

---

## What "Failed to fetch" Means

This error occurs **before** the request reaches the server. Possible causes:

1. **CORS preflight failed** - Browser blocked OPTIONS request
2. **Network connectivity** - Can't reach server (but curl works, so unlikely)
3. **Browser security** - Extension or browser blocking request
4. **SSL/Certificate** - Certificate issue (unlikely, HTTPS works)

---

## Debug Steps

### 1. Check Browser Console
The improved error logging should show:
- `🚀 Starting bot: [bot-id]`
- `📡 API URL: [full-url]`
- `🔗 TRADING_BRIDGE_URL: [url]`
- `❌ Fetch failed (network/CORS error):` with details

### 2. Check Network Tab
1. Right-click page → Inspect → Network tab
2. Click "Start Bot"
3. Look for the `POST /bots/{id}/start` request
4. Check:
   - **Status:** (red?) Failed? CORS error?
   - **Type:** preflight? xhr?
   - **Response:** Any error message?

### 3. Test CORS Preflight
The browser sends an OPTIONS request first. Check if it succeeds:
- Look for `OPTIONS /bots/{id}/start` in Network tab
- Does it return 200 with CORS headers?

---

## Current CORS Config

```python
ALLOWED_ORIGINS = [
    "https://app.pipelabs.xyz",  # ✅ Frontend origin
    "https://pipelabs.xyz",
    "http://localhost:3000",
    "http://localhost:5173",
]
```

**Question:** Is the frontend actually running on `https://app.pipelabs.xyz`?

---

## Possible Fixes

### If CORS Issue:
1. Verify frontend origin matches exactly
2. Check if Railway is adding extra CORS headers
3. Try adding `*` temporarily to test (then remove)

### If Browser Blocking:
1. Check browser extensions (ad blockers, privacy tools)
2. Try incognito mode
3. Check browser console for security warnings

---

## Next Steps

1. Check browser console for the detailed logs we added
2. Check Network tab for the actual request
3. Share:
   - What URL is being called?
   - What's the status in Network tab?
   - Any CORS errors in console?
