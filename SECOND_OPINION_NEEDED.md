# Second Opinion Needed - Start Bot "Failed to fetch" Issue

**Status:** We've tried multiple approaches but still getting "Network error: Failed to fetch"

**Date:** February 7, 2026

---

## Current Problem

When user clicks "Start Bot", they get: **"Failed to fetch"** error

This happens **before** the request reaches the server (browser is blocking it).

---

## What We've Tried

### 1. Backend Fixes
- ✅ Fixed Request injection syntax error (parameter ordering)
- ✅ Removed `= None` default from Request parameter
- ✅ Reordered parameters to fix Python syntax

### 2. Frontend Fixes
- ✅ Added per-bot loading state (fixed multiple bots starting issue)
- ✅ Added detailed error logging
- ✅ Added network error catching
- ✅ Improved error messages

### 3. CORS Checks
- ✅ Verified CORS config includes `https://app.pipelabs.xyz`
- ✅ Tested OPTIONS preflight with curl (works)
- ✅ Backend responds to curl requests (404 expected for test bot)

---

## Current State

**Backend:** 
- Syntax errors fixed ✅
- Request injection fixed ✅
- CORS configured ✅
- Endpoint exists: `POST /bots/{bot_id}/start` ✅

**Frontend:**
- Per-bot loading state working ✅
- Error logging added ✅
- Still getting "Failed to fetch" ❌

**Test Results:**
- `curl` to backend works (404 for test bot, which is expected)
- OPTIONS preflight works
- But browser fetch() fails with "Failed to fetch"

---

## What "Failed to fetch" Usually Means

1. **CORS blocking** - But we've verified CORS config
2. **Browser extension blocking** - Ad blocker, privacy tool
3. **Network issue** - But curl works, so unlikely
4. **SSL/Certificate** - Unlikely, HTTPS works
5. **Request format issue** - Maybe headers or method?

---

## Questions for Dev

1. **Is there a known issue with this endpoint?**
   - Has it worked before?
   - Any recent changes that broke it?

2. **Should we check Railway logs?**
   - Are requests even reaching the backend?
   - Any errors in logs when start bot is clicked?

3. **Is the endpoint path correct?**
   - Current: `POST /bots/{bot_id}/start`
   - Is this the right path?

4. **Are headers correct?**
   - We're sending: `Content-Type`, `X-Wallet-Address`, `Authorization`
   - Are these required? Any missing?

5. **Alternative approach?**
   - Should we use a different endpoint?
   - Is there a different way to start bots?

6. **Browser-specific issue?**
   - Should we test in different browsers?
   - Is there a known Safari/Chrome issue?

---

## What We Need

**Before trying more fixes, please advise:**

1. **What should we check first?** (Railway logs? Different endpoint? Headers?)
2. **Has this endpoint worked before?** (If yes, what changed?)
3. **Is there a simpler way to test?** (Can you test it directly and share what works?)
4. **Should we try a different approach?** (Different endpoint? Different method?)

---

## Code References

**Backend endpoint:**
- File: `app/bot_routes.py`
- Line: 795
- Function: `start_bot(bot_id: str, request: Request, ...)`

**Frontend call:**
- File: `src/services/api.js`
- Function: `startBot(botId)`
- URL: `${TRADING_BRIDGE_URL}/bots/${botId}/start`

**CORS config:**
- File: `app/main.py`
- Line: 310-315
- Origins: `["https://app.pipelabs.xyz", ...]`

---

**We've tried multiple approaches but hitting a wall. Need second opinion on best way forward.**
