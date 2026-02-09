# BitMart Balance Not Showing - Debug Guide

## ⚠️ Important Clarification

**BitMart balances come from Exchange API (using API keys), NOT from private keys.**

- **Private keys** = For Solana/EVM wallet trading (on-chain)
- **API keys** = For BitMart exchange trading (CEX)

---

## Current Issue

**User sees:**
- "1 exchanges" ✅ (BitMart connector exists)
- "0 tokens" ❌ (No balances showing)
- Balance: $0 ❌ (Should show USDT and SHARP)

---

## How Balance Fetching Works

### Flow:
1. Frontend calls `/api/clients/balances?wallet_address=0xB4E3...`
2. Backend looks up client by wallet address
3. Gets `account_identifier` (e.g., `client_new_sharp_foundation`)
4. Calls `sync_connectors_to_exchange_manager()` - loads BitMart API keys from DB
5. Queries BitMart API using ccxt: `exchange.fetch_balance()`
6. Returns array of token balances

### Code Location:
- **Balance fetching**: `app/services/exchange.py` line 108-132
- **Filters non-zero**: Only shows balances > 0 (line 119)
- **Returns array**: `app/api/client_data.py` line 118-125

---

## Possible Issues

### 1. **API Keys Not Working**
- BitMart API keys might be incorrect
- IP whitelist not set (needs QuotaGuard IP: `3.222.129.4`)
- API keys don't have balance read permissions

### 2. **Balance Fetch Failing Silently**
- Error might be caught and logged but not shown to user
- Check Railway logs for: "Failed to get balances from bitmart"

### 3. **Frontend Not Displaying Tokens**
- Backend returns array of tokens
- Frontend might only show total USDT, not individual tokens
- Need to check frontend code

### 4. **Connector Not Syncing**
- BitMart connector exists in DB but not loading into exchange_manager
- Check logs for: "Synced connector bitmart to exchange_manager"

---

## Debugging Steps

### Step 1: Check Railway Logs

Look for these log messages:
```
✅ Synced connector bitmart to exchange_manager for client_new_sharp_foundation
Failed to get balances from bitmart: [error message]
```

### Step 2: Test Admin Balance Endpoint

After deployment, test:
```bash
GET /admin/clients/{client_id}/balances
```

This will show:
- Individual token balances
- Any errors
- Whether connectors are loaded

### Step 3: Verify BitMart API Keys

In admin UI → New Sharp Foundation → API Keys:
- Does BitMart show with checkmark?
- Are API key, secret, and memo all filled?
- Are they correct?

### Step 4: Check IP Whitelist

BitMart requires IP whitelisting:
- Is `3.222.129.4` (QuotaGuard IP) whitelisted in BitMart?
- If not, API calls will fail

---

## Expected Response Format

The `/api/clients/balances` endpoint returns:

```json
[
  {
    "exchange": "bitmart",
    "asset": "USDT",
    "total": 1500.0,
    "free": 1500.0,
    "used": 0.0,
    "usd_value": 0
  },
  {
    "exchange": "bitmart",
    "asset": "SHARP",
    "total": 8000000.0,
    "free": 8000000.0,
    "used": 0.0,
    "usd_value": 0
  }
]
```

---

## Next Steps

1. **Check Railway logs** for balance fetch errors
2. **Test admin endpoint** after deployment
3. **Verify IP whitelist** in BitMart dashboard
4. **Check frontend** - does it display individual tokens or just total?

---

## Quick Test

After Railway deploys, you can test directly:

```bash
# Get client_id for New Sharp Foundation, then:
curl "https://trading-bridge-production.up.railway.app/admin/clients/{client_id}/balances" \
  -H "Authorization: Bearer {admin_token}" \
  -H "X-Wallet-Address: {admin_wallet}"
```

This will show raw balance data and any errors.
