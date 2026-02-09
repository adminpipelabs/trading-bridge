# Frontend-Backend Connection Verification Guide

## 🔍 Problem: Balances Showing 0

**Root Cause:** Frontend may not be calling the correct endpoint or not handling the response correctly.

---

## ✅ Step 1: Verify Backend Endpoint is Working

### Test the Backend Directly

```bash
# Replace with your actual values
ACCOUNT="your_account_identifier"
WALLET="your_wallet_address"
API_URL="https://trading-bridge-production.up.railway.app"

# Test endpoint
curl -X GET "${API_URL}/api/bots?account=${ACCOUNT}&include_balances=true" \
  -H "X-Wallet-Address: ${WALLET}" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "bots": [
    {
      "id": "...",
      "name": "SHARP Volume Bot - BitMart",
      "status": "stopped",
      "bot_type": "volume",
      "connector": "bitmart",
      "balance": {
        "available": {
          "SHARP": 1000.0,
          "USDT": 50.0
        },
        "locked": {
          "SHARP": 0,
          "USDT": 0
        },
        "volume_24h": 0,
        "trades_24h": {"buys": 0, "sells": 0}
      }
    }
  ]
}
```

**If this works:** Backend is fine, frontend needs fixing.
**If this fails:** Check Railway logs for errors.

---

## ✅ Step 2: Check What Frontend is Actually Calling

### Check Browser Network Tab

1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Refresh dashboard
4. Look for requests to `/bots` or `/api/bots`

**What to look for:**
- ✅ Request URL should be: `/api/bots?account=...&include_balances=true`
- ✅ Request headers should include: `X-Wallet-Address: ...`
- ✅ Response should have `balance` field in each bot object

**Common Issues:**
- ❌ Frontend calling `/bots` without `/api` prefix
- ❌ Frontend not passing `include_balances=true`
- ❌ Frontend not sending `X-Wallet-Address` header
- ❌ Frontend calling wrong endpoint entirely

---

## ✅ Step 3: Verify Frontend API Service

### Check Frontend API Configuration

**File:** `ai-trading-ui/src/services/api.js` (or similar)

**Should have:**
```javascript
const API_BASE = process.env.REACT_APP_API_URL || 'https://trading-bridge-production.up.railway.app';

export const tradingBridge = {
  async getBots(account, walletAddress) {
    const response = await fetch(
      `${API_BASE}/api/bots?account=${account}&include_balances=true`,
      {
        headers: {
          'X-Wallet-Address': walletAddress,
          'Content-Type': 'application/json'
        }
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch bots: ${response.statusText}`);
    }
    return response.json();
  }
};
```

**Check:**
- ✅ `API_BASE` includes `/api` prefix OR endpoint includes `/api/bots`
- ✅ `include_balances=true` is in the URL
- ✅ `X-Wallet-Address` header is being sent
- ✅ Response is being parsed correctly

---

## ✅ Step 4: Verify Frontend Component

### Check ClientDashboard Component

**File:** `ai-trading-ui/src/pages/ClientDashboard.jsx`

**Should be calling:**
```javascript
const fetchBots = async () => {
  try {
    const data = await tradingBridge.getBots(account, walletAddress);
    setBots(data.bots || []);
  } catch (err) {
    console.error('Failed to fetch bots:', err);
  }
};
```

**Check:**
- ✅ Component calls `tradingBridge.getBots()` with correct parameters
- ✅ Component extracts `data.bots` from response
- ✅ Component accesses `bot.balance.available` and `bot.balance.locked`
- ✅ Component displays balance data correctly

---

## ✅ Step 5: Check Response Format Handling

### Backend Returns:
```json
{
  "bots": [
    {
      "id": "...",
      "name": "...",
      "balance": {
        "available": {"SHARP": 1000, "USDT": 50},
        "locked": {"SHARP": 0, "USDT": 0}
      }
    }
  ]
}
```

### Frontend Should Access:
```javascript
// In BotCard component
const available = bot.balance?.available || {};
const locked = bot.balance?.locked || {};

// Display
{Object.entries(available).map(([asset, amount]) => (
  <div key={asset}>{amount} {asset}</div>
))}
```

**Common Issues:**
- ❌ Frontend looking for `bot.available` instead of `bot.balance.available`
- ❌ Frontend not checking if `bot.balance` exists
- ❌ Frontend not handling empty balance objects

---

## 🔧 Quick Fixes

### Fix 1: Add `/api` Prefix

**If frontend is calling `/bots` instead of `/api/bots`:**

```javascript
// Wrong
const response = await fetch(`${API_BASE}/bots?...`);

// Correct
const response = await fetch(`${API_BASE}/api/bots?...`);
```

### Fix 2: Ensure `include_balances=true`

```javascript
// Wrong
const response = await fetch(`${API_BASE}/api/bots?account=${account}`);

// Correct
const response = await fetch(`${API_BASE}/api/bots?account=${account}&include_balances=true`);
```

### Fix 3: Add X-Wallet-Address Header

```javascript
// Wrong
const response = await fetch(`${API_BASE}/api/bots?...`);

// Correct
const response = await fetch(`${API_BASE}/api/bots?...`, {
  headers: {
    'X-Wallet-Address': walletAddress
  }
});
```

### Fix 4: Handle Balance Field Correctly

```javascript
// Wrong
const available = bot.available || {};

// Correct
const available = bot.balance?.available || {};
const locked = bot.balance?.locked || {};
```

---

## 📊 Debug Checklist

- [ ] Backend endpoint works when tested directly (curl/Postman)
- [ ] Frontend is calling `/api/bots` (check Network tab)
- [ ] Frontend is passing `include_balances=true`
- [ ] Frontend is sending `X-Wallet-Address` header
- [ ] Frontend is accessing `bot.balance.available` (not `bot.available`)
- [ ] Frontend is displaying balance data correctly
- [ ] Railway logs show `/bots` endpoint being called
- [ ] Railway logs show balance fetch attempts

---

## 🚨 Most Likely Issues

1. **Frontend calling wrong endpoint** - Check Network tab
2. **Frontend not passing `include_balances=true`** - Check URL params
3. **Frontend accessing wrong field** - Should be `bot.balance.available`, not `bot.available`
4. **Frontend not sending `X-Wallet-Address` header** - Check headers in Network tab
5. **CORS issues** - Check browser console for CORS errors

---

## 📝 Next Steps

1. **Check browser Network tab** - See what frontend is actually calling
2. **Check browser Console** - Look for JavaScript errors
3. **Check Railway logs** - See if backend is receiving requests
4. **Test backend directly** - Use curl to verify backend works
5. **Fix frontend** - Update API calls based on findings

---

## ✅ Expected Flow

1. Frontend calls: `GET /api/bots?account=...&include_balances=true`
2. Backend receives request with `X-Wallet-Address` header
3. Backend fetches bots from database
4. Backend calls `get_bot_stats()` for each bot
5. Backend syncs connectors and fetches balances from exchange
6. Backend returns bots with `balance` field
7. Frontend displays `bot.balance.available` and `bot.balance.locked`

---

## 🎯 Summary

**The backend is ready and working.** The issue is likely:
- Frontend calling wrong endpoint
- Frontend not passing correct parameters
- Frontend not handling response format correctly

**Check the browser Network tab to see exactly what the frontend is calling!**
