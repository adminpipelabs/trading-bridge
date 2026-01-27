# Dev Help: Frontend Not Showing Dashboard Data

## Current Status

### ✅ Backend Working
- `/api/exchange/dashboard/client_sharp` returns **real data**:
  ```json
  {
    "balance": {
      "total_usdt": 42.75342157,
      "balances": [
        {"exchange": "bitmart", "asset": "USDT", "total": 42.75, "usd_value": 42.75},
        {"exchange": "bitmart", "asset": "SHARP", "total": 3218.52, "usd_value": 0}
      ]
    },
    "volume": {"traded": 56.69, "trade_count": 8},
    "recent_trades": [...]
  }
  ```

### ❌ Frontend Showing $0.00
- Total Balance: **$0.00**
- P&L: **$0.00**
- Volume: **$0.00**
- 0 exchanges
- 0 trades

---

## Possible Issues

### 1. **`clientAccount` Not Set**

Frontend code (line 1861):
```javascript
if (clientAccount) {
  const dashboardData = await clientAPI.getDashboard(clientAccount);
  // ...
}
```

**Check**: Is `clientAccount` being set correctly?
- Line 1849: `setClientAccount(clientInfo.account_identifier)`
- Depends on `getClientByWallet()` succeeding

**Debug**: Add console.log:
```javascript
console.log('clientAccount:', clientAccount);
console.log('dashboardData:', dashboardData);
```

### 2. **API Call Failing**

Frontend might be:
- Calling wrong endpoint
- Getting CORS error
- Getting 404/500 error
- Response format mismatch

**Check Browser Console**:
- Network tab → Look for `/api/exchange/dashboard/client_sharp`
- Check status code (200? 404? 500?)
- Check response body

### 3. **Response Transformation Issue**

Backend returns:
```json
{
  "balance": {
    "balances": [
      {"exchange": "bitmart", "asset": "USDT", "usd_value": 42.75},
      {"exchange": "bitmart", "asset": "SHARP", "usd_value": 0}
    ]
  }
}
```

Frontend expects:
```javascript
setBalances(dashboardData.balance?.balances || []);
```

**Issue**: `usd_value` for SHARP is 0 (only USDT has usd_value set).

Frontend calculates:
```javascript
const totalBalance = balances.reduce((sum, b) => sum + (b.usd_value || 0), 0);
```

**Result**: Only counts USDT (42.75), but screenshot shows $0.00, so data isn't loading at all.

### 4. **Frontend Not Deployed**

Check if frontend code with `getDashboard()` call is deployed.

---

## Debugging Steps Needed

### Step 1: Check Browser Console

1. Open client dashboard in browser
2. DevTools → Console tab
3. Look for:
   - `clientAccount: ...` (should be `client_sharp`)
   - `dashboardData: ...` (should show balance data)
   - Any errors?

### Step 2: Check Network Tab

1. DevTools → Network tab
2. Filter: `dashboard` or `exchange`
3. Check:
   - Is request being made? (`GET /api/exchange/dashboard/client_sharp`)
   - Status code? (200? 404? 500?)
   - Response body? (should show balances)

### Step 3: Check React State

Add temporary logging:
```javascript
console.log('balances:', balances);
console.log('portfolio:', portfolio);
console.log('volume:', volume);
console.log('totalBalance:', totalBalance);
```

---

## Code Check

### Frontend (`AdminDashboard.jsx` line 1861-1876):

```javascript
if (clientAccount) {
  const dashboardData = await clientAPI.getDashboard(clientAccount);
  setPortfolio({
    total_pnl: dashboardData.pnl?.total || 0,
    active_bots: dashboardData.bots?.active || 0,
    total_bots: dashboardData.bots?.total || 0
  });
  setBalances(dashboardData.balance?.balances || []);
  setTrades(dashboardData.recent_trades || []);
  setVolume({
    total_volume: dashboardData.volume?.traded || 0,
    trade_count: dashboardData.volume?.trade_count || 0
  });
}
```

**Questions**:
1. Is `clientAccount` set? (Check line 1849)
2. Is `getDashboard()` being called?
3. Is `dashboardData` received?
4. Are state setters being called?

---

## Likely Root Cause

**Hypothesis**: `clientAccount` is `null` or `undefined`, so the code falls through to the `else` block (line 1891), which calls individual endpoints that require `wallet_address` parameter, but those might be failing or returning empty data.

**Check**: Line 1891-1902 - is this code path being executed instead?

---

## Files to Check

- `src/pages/AdminDashboard.jsx` line 1844-1909 - `loadClientData` function
- `src/services/api.js` line 254 - `getDashboard` method
- Browser console - actual API calls and responses

---

## Request for Dev

**Please check**:
1. Browser console logs - what's `clientAccount` value?
2. Network tab - is `/api/exchange/dashboard/client_sharp` being called?
3. Response - what does the API actually return?
4. State - are `balances`, `portfolio`, `volume` being set?

**Backend is working** - need to debug frontend integration.
