# Dev Review Needed: CORS Credentials Mismatch Fix

**Status:** Changes made but NOT deployed - awaiting your approval

**Date:** February 8, 2026

---

## 🔍 **Problem Identified**

**Error:** "Failed to start bot: Network error: Cannot reach https://trading-bridge-production.up.railway.app/bots/{id}/start"

**Root Cause:** CORS credentials mismatch
- **Backend:** `allow_credentials=True` in CORS middleware
- **Frontend:** `credentials: 'omit'` in fetch options
- **Result:** Browser silently blocks request before it reaches server

---

## ✅ **CORS Headers Verified (Backend is Correct)**

Tested OPTIONS preflight request:
```bash
curl -X OPTIONS .../bots/{id}/start \
  -H "Origin: https://app.pipelabs.xyz" \
  -H "Access-Control-Request-Method: POST"
```

**Response Headers (All Correct):**
```
access-control-allow-origin: https://app.pipelabs.xyz ✅
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS ✅
access-control-allow-headers: content-type,x-wallet-address ✅
access-control-allow-credentials: true ✅
```

**Backend CORS config is correct** - no changes needed.

---

## 🔧 **Frontend Changes Made (NOT Deployed)**

**File:** `ai-trading-ui/src/services/api.js`

**Change:** Updated `apiCall` function fetch options:

```javascript
// BEFORE:
const fetchOptions = {
  method: options.method || 'GET',
  headers: headers,
  ...(options.body && { body: options.body }),
};

// AFTER:
const fetchOptions = {
  method: options.method || 'GET',
  headers: headers,
  mode: 'cors',              // ← Added explicit CORS mode
  credentials: 'include',    // ← Changed from 'omit' to 'include'
  ...(options.body && { body: options.body }),
};
```

**Why:** When backend has `allow_credentials=True`, frontend MUST send `credentials: 'include'` or browser blocks the request.

---

## 📋 **Commits Made (NOT Pushed to Production)**

**Frontend (`ai-trading-ui`):**
1. `fda07bc` - "FIX: Use apiCall wrapper for startBot - fixes Failed to fetch error"
2. `76821dd` - "FIX: Add explicit CORS mode and credentials settings to fetch"
3. `390f633` - "FIX: Change credentials to include to match backend allow_credentials=True"

**Backend (`trading-bridge`):**
- No changes needed - CORS config is already correct

---

## ❓ **Questions for Dev**

1. **Is `allow_credentials=True` necessary?**
   - We're using Bearer tokens, not cookies
   - Could we set `allow_credentials=False` instead?
   - Or is there a reason we need credentials?

2. **Should I deploy these frontend changes?**
   - The fix matches backend config
   - But want your approval first

3. **Alternative approach:**
   - Change backend to `allow_credentials=False`
   - Keep frontend as `credentials: 'omit'`
   - Which is better?

---

## 🧪 **Testing**

**Before deploying, please verify:**
1. Does admin dashboard use same `apiCall` function?
2. Does admin bot start work? (If yes, what credentials setting does it use?)
3. Are there any other endpoints that might be affected?

---

## 📝 **Recommendation**

**Option 1 (Recommended):** Deploy frontend fix
- Matches existing backend config
- Minimal risk
- Fixes the issue

**Option 2:** Change backend to `allow_credentials=False`
- More secure (no credentials sent)
- Requires backend redeploy
- Need to verify no other code depends on credentials

**Please advise which approach you prefer before I deploy anything.**
