# Dev Research Needed: Start Bot "Failed to fetch" Issue

**Status:** Still failing after multiple attempts - need dev investigation

**Date:** February 8, 2026

---

## The Problem

**Client clicks "Start Bot" → Gets "Failed to fetch" error**

**Key Facts:**
- ✅ Backend is running (curl `/health` returns 200)
- ✅ Backend endpoint exists (`POST /bots/{id}/start`)
- ✅ CORS preflight works (curl OPTIONS returns 200 with correct headers)
- ✅ Backend responds to curl POST (returns 401, which is expected)
- ❌ Browser fetch() fails with "Failed to fetch" - request never reaches server

---

## What We've Tried

### Backend Changes:
1. ✅ Fixed Request injection syntax (parameter ordering)
2. ✅ Fixed authorization logic (wallet auth → token fallback)
3. ✅ Verified CORS config includes `https://app.pipelabs.xyz`
4. ✅ Verified CORS allows all headers (`allow_headers=["*"]`)

### Frontend Changes:
1. ✅ Added per-bot loading state (fixed multiple bots starting)
2. ✅ Simplified fetch call (removed timeout, credentials, explicit CORS mode)
3. ✅ Always set Content-Type header
4. ✅ Added empty JSON body `{}` to POST
5. ✅ Tried direct fetch (bypassed apiCall wrapper)
6. ✅ Reverted to apiCall wrapper (same as admin uses)

### Tests Performed:
- ✅ curl POST works → backend responds
- ✅ curl OPTIONS works → CORS headers correct
- ✅ Backend health check works
- ❌ Browser fetch() fails → "Failed to fetch"

---

## The Mystery

**Why does curl work but browser fetch() fail?**

**Possible causes:**
1. Browser CORS preflight failing silently (even though curl OPTIONS works)
2. Browser security policy blocking custom headers (`X-Wallet-Address`)
3. Request format issue that only affects browsers
4. Something wrong with how browser sends the request

---

## What We Need

**Please investigate:**

1. **Check Railway logs** when client clicks "Start Bot":
   - Does the request even reach the backend?
   - Any errors in logs?
   - What's the actual request that arrives?

2. **Compare admin vs client:**
   - Admin can start bots → what's different?
   - Same endpoint, same function → why does admin work?
   - Different headers? Different auth?

3. **Test the actual request:**
   - Can you test `POST /bots/{id}/start` from browser console?
   - What exact error do you see?
   - Does OPTIONS preflight succeed in browser?

4. **Check if it's a known issue:**
   - Has this worked before?
   - Any recent changes that broke it?
   - Is there a workaround?

---

## Current Code State

**Backend:** `35ea901` - Fixed authorization logic
**Frontend:** `40ff0d2` - Added empty JSON body, simplified fetch

**Endpoint:** `POST /bots/{bot_id}/start`
- Location: `app/bot_routes.py` line 795
- Auth: Wallet address OR Authorization token
- CORS: Configured for `https://app.pipelabs.xyz`

---

## Questions for Dev

1. **Has this endpoint worked before for clients?**
2. **What's different between admin and client requests?**
3. **Should we check Railway logs for actual errors?**
4. **Is there a simpler way to test this?**
5. **Could it be a browser-specific issue we're missing?**

---

**We've tried many approaches but hitting a wall. Need dev to investigate the root cause.**
