# Dev Help: Dashboard Endpoint Not Working

## Current Status

### ✅ Backend Deployment
- **Endpoint exists**: `/api/exchange/dashboard/{account}`
- **Tested**: Returns data successfully
- **Logs**: No errors, startup successful
- **Database**: Initialized correctly

### ❓ Frontend Issue
- User reports "does not work"
- Need to verify frontend is calling endpoint correctly

---

## What's Working

### Backend Test (Success):
```bash
curl https://trading-bridge-production.up.railway.app/api/exchange/dashboard/client_sharp
```

**Returns**:
```json
{
  "account": "client_sharp",
  "balance": {"total_usdt": 0.0, "balances": []},
  "pnl": {"total": 0.0, "by_pair": {}},
  "volume": {"traded": 0, "trade_count": 0},
  "recent_trades": [],
  "bots": {"active": 1, "total": 1}
}
```

✅ **Endpoint is working!**

---

## Possible Issues

### 1. **Frontend Not Deployed**
- Check if `ai-trading-ui` was deployed to Railway
- Verify frontend code includes `clientAPI.getDashboard()` call

### 2. **Account Identifier Not Found**
- Frontend needs `clientAccount` (account_identifier) to call endpoint
- Check if `getClientByWallet()` is working
- Verify `clientAccount` state is set correctly

### 3. **CORS Issue**
- Check browser console for CORS errors
- Verify `trading-bridge` CORS settings allow frontend origin

### 4. **Frontend Code Not Updated**
- Check if `AdminDashboard.jsx` has the new `getDashboard()` call
- Verify `api.js` has `getDashboard()` method

---

## Debugging Steps Needed

### Step 1: Check Frontend Deployment
```bash
# Check if frontend was deployed
curl https://ai-trading-ui-production.up.railway.app
```

### Step 2: Check Browser Console
1. Open client dashboard in browser
2. Open DevTools → Console tab
3. Look for:
   - API call errors
   - Network request failures
   - CORS errors
   - `clientAccount` is `null` or `undefined`

### Step 3: Check Network Tab
1. DevTools → Network tab
2. Filter: `dashboard` or `exchange`
3. Check:
   - Is request being made?
   - What's the URL?
   - Status code? (200? 404? 500?)
   - Response body?

### Step 4: Verify Account Identifier
```javascript
// In browser console on client dashboard
console.log('clientAccount:', clientAccount);
console.log('user:', user);
```

---

## Code Check

### Frontend Should Have:
1. ✅ `clientAPI.getDashboard(accountIdentifier)` in `api.js`
2. ✅ Call to `getDashboard()` in `AdminDashboard.jsx`
3. ✅ `clientAccount` state set from `getClientByWallet()`

### Backend Has:
1. ✅ `/api/exchange/dashboard/{account}` endpoint
2. ✅ Router included in `main.py`
3. ✅ Auto-sync connectors function

---

## Questions for Dev

1. **Is frontend deployed?** Check Railway `ai-trading-ui` service
2. **What error appears in browser console?** Check DevTools
3. **Is `clientAccount` being set?** Check React state
4. **Are API calls being made?** Check Network tab
5. **What does "does not work" mean?** 
   - No data shown?
   - Error message?
   - Page doesn't load?
   - API call fails?

---

## Files to Check

### Backend (✅ Working):
- `app/exchange_routes.py` - Endpoint exists
- `app/main.py` - Router included
- `app/api/client_data.py` - Sync function exists

### Frontend (❓ Need to verify):
- `src/services/api.js` - Has `getDashboard()`?
- `src/pages/AdminDashboard.jsx` - Calls `getDashboard()`?
- `src/pages/AdminDashboard.jsx` - Sets `clientAccount`?

---

## Next Steps

1. **Check frontend deployment** - Is `ai-trading-ui` deployed?
2. **Check browser console** - What errors appear?
3. **Check network requests** - Are API calls being made?
4. **Verify account identifier** - Is `clientAccount` set correctly?

**Full details**: Backend is working, need to debug frontend integration.
