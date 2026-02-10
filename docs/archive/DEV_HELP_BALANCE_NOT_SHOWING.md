# URGENT: Balance Not Showing - Developer Help Needed

## 🚨 Problem
- Dashboard loads but shows **0 balances** for all bots
- Client lost because they saw nothing
- Balance fetching should work (works in 3 mins locally with Hummingbot pattern)

## ✅ What We've Fixed
1. ✅ Simplified balance extraction to match Hummingbot exactly: `balance.get("free", {}).get(currency, 0)`
2. ✅ Added timeouts to prevent dashboard hanging (5s per bot, 10s total)
3. ✅ Fixed balance format access (was trying `balance[currency]['free']`, now `balance['free'][currency]`)
4. ✅ Removed `{'type': 'spot'}` parameter (not needed when markets loaded)
5. ✅ Ensured markets load before balance fetch

## 🔍 What to Check (In Order)

### 1. **Are API Keys Being Read from Database?**
Check Railway logs for:
```
🔄 Syncing connectors for account: {account}
✅ Found {N} connector(s) in 'connectors' table
✅ Found {N} credential(s) in 'exchange_credentials' table
```

**If you see:**
- `❌ No connectors found` → API keys aren't in database
- `⚠️  No connectors in 'connectors' table` → Check `exchange_credentials` table

**Action:** Verify API keys exist in database:
```sql
-- Check connectors table
SELECT client_id, name, api_key IS NOT NULL as has_key 
FROM connectors 
WHERE client_id = (SELECT id FROM clients WHERE account_identifier = 'client_new_sharp_foundation');

-- Check exchange_credentials table
SELECT exchange, api_key_encrypted IS NOT NULL as has_key 
FROM exchange_credentials 
WHERE client_id = (SELECT id FROM clients WHERE account_identifier = 'client_new_sharp_foundation');
```

### 2. **Is Exchange Being Created Correctly?**
Check logs for:
```
✅ Synced connector 'bitmart' from 'connectors' table to exchange_manager
Added bitmart connector to account {account}
```

**If missing:** Exchange isn't being created → connector sync is failing

**Action:** Check `app/services/exchange.py` `add_connector()` method - is it being called?

### 3. **Is Balance Actually Being Fetched?**
Check logs for:
```
🔍 Fetching balance for {connector_name} bot {bot_id}
✅ Balance fetched: {N} currencies
✅ Balance: SHARP={amount} free, {amount} locked; USDT={amount} free, {amount} locked
```

**If you see:**
- `❌ Timeout fetching balance` → API call is hanging
- `⚠️  BitMart ccxt AttributeError bug` → BitMart API returning error
- No balance logs at all → Balance fetch isn't being called

### 4. **Test Balance Fetching Directly**
Run this to test if balance fetching works at all:

```python
import asyncio
import ccxt.async_support as ccxt

async def test_balance():
    # Get API keys from database
    from app.database import SessionLocal
    from app.cex_volume_bot import decrypt_credential
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        # Get credentials
        creds = db.execute(text("""
            SELECT api_key_encrypted, api_secret_encrypted, passphrase_encrypted
            FROM exchange_credentials
            WHERE client_id = (SELECT id FROM clients WHERE account_identifier = 'client_new_sharp_foundation')
            AND exchange = 'bitmart'
        """)).first()
        
        if not creds:
            print("❌ No credentials found")
            return
        
        api_key = decrypt_credential(creds.api_key_encrypted)
        api_secret = decrypt_credential(creds.api_secret_encrypted)
        memo = decrypt_credential(creds.passphrase_encrypted) if creds.passphrase_encrypted else None
        
        # Create exchange EXACTLY like Hummingbot
        exchange = ccxt.bitmart({
            'apiKey': api_key,
            'secret': api_secret,
            'uid': memo,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Load markets
        await exchange.load_markets()
        print(f"✅ Markets loaded: {len(exchange.markets)} markets")
        
        # Fetch balance
        balance = await exchange.fetch_balance()
        print(f"✅ Balance fetched")
        print(f"   Free currencies: {list(balance.get('free', {}).keys())[:10]}")
        
        # Check SHARP and USDT
        sharp_free = balance.get("free", {}).get("SHARP", 0)
        usdt_free = balance.get("free", {}).get("USDT", 0)
        print(f"   SHARP: {sharp_free}")
        print(f"   USDT: {usdt_free}")
        
        await exchange.close()
        
    finally:
        db.close()

asyncio.run(test_balance())
```

**If this works:** Balance fetching code is fine, issue is in how we're calling it
**If this fails:** API keys are wrong or BitMart API is rejecting requests

### 5. **Check Exchange Manager State**
The exchange might be created but not stored correctly. Check:

```python
from app.services.exchange import exchange_manager

account = exchange_manager.get_account('client_new_sharp_foundation')
if account:
    print(f"Account found: {account.name}")
    print(f"Connectors: {list(account.connectors.keys())}")
    for name, exchange in account.connectors.items():
        print(f"  {name}: {type(exchange).__name__}")
        if hasattr(exchange, 'apiKey'):
            print(f"    API Key: {exchange.apiKey[:4]}...{exchange.apiKey[-4:]}")
else:
    print("❌ Account not found in exchange_manager")
```

## 🎯 Expected Flow

1. **Client logs in** → Frontend calls `/api/bots` or `/api/bots/{bot_id}/stats`
2. **Backend syncs connectors** → `sync_connectors_to_exchange_manager(account, db)`
   - Reads from `connectors` table OR `exchange_credentials` table
   - Creates exchange instance: `ccxt.bitmart(config)`
   - Stores in `exchange_manager.accounts[account].connectors['bitmart']`
3. **Backend fetches balance** → `exchange.fetch_balance()`
   - Loads markets if needed
   - Calls BitMart API
   - Returns: `{"free": {"SHARP": 8381807.12, "USDT": 72.83}, "used": {...}, "total": {...}}`
4. **Backend extracts balances** → `balance.get("free", {}).get("SHARP", 0)`
5. **Backend returns to frontend** → `{"available": {"SHARP": 8381807.12, "USDT": 72.83}}`

## 🐛 Common Issues

### Issue 1: Connector Sync Failing
**Symptoms:** No connectors in exchange_manager
**Check:** Logs show `❌ No connectors found` or `Failed to sync connector`
**Fix:** Verify API keys exist in database, check decryption key

### Issue 2: Exchange Not Created with Correct Config
**Symptoms:** Exchange created but balance fetch fails
**Check:** Logs show exchange created but no balance logs
**Fix:** Verify `add_connector()` is setting `options: {defaultType: 'spot'}` for BitMart

### Issue 3: Balance Fetch Timing Out
**Symptoms:** `❌ Timeout fetching balance`
**Check:** BitMart API responding? Network issues? IP whitelist?
**Fix:** Check BitMart API status, verify IP whitelist

### Issue 4: Balance Extraction Wrong
**Symptoms:** Balance fetched but shows 0
**Check:** Logs show `✅ Balance fetched: {N} currencies` but `Balance: SHARP=0`
**Fix:** Verify balance structure matches expected format

## 📋 Quick Test Commands

```bash
# Test balance endpoint directly
curl -H "X-Wallet-Address: {wallet}" \
  "https://trading-bridge-production.up.railway.app/api/bots/{bot_id}/stats"

# Check if connector sync works
curl "https://trading-bridge-production.up.railway.app/api/clients/debug?wallet_address={wallet}"
```

## 🎯 Next Steps for Dev

1. **Check Railway logs** for the patterns above
2. **Run the test script** to verify balance fetching works directly
3. **Check database** to verify API keys exist
4. **Check exchange_manager** state to see if connectors are loaded
5. **Add more logging** if needed to trace the exact failure point

## 💡 Key Insight

The user can do this in **3 minutes locally** with Hummingbot:
```python
exchange = ccxt.bitmart({'apiKey': key, 'secret': secret, 'uid': memo})
await exchange.load_markets()
balance = await exchange.fetch_balance()
# Done. balance['free']['SHARP'] works.
```

Our code should do **exactly the same thing**. If it doesn't work, something is wrong with:
- How we're reading API keys from database
- How we're creating the exchange instance
- How we're calling fetch_balance
- How we're extracting the balance data

**The pattern is simple - if it's not working, we're overcomplicating it.**
