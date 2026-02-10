# Spread Bot 1401 Unauthorized Error - SOLUTION FOUND ✅

## ✅ RESOLVED

**Date:** February 10, 2026  
**Environment:** Production (Hetzner VPS)  
**Root Cause:** API Key missing **Read** permission (Trade permission works, Read does not)  
**Solution:** Enable Read permission on Coinstore API key dashboard

**See `SPREAD_BOT_1401_SOLUTION.md` for complete fix instructions.**

---

## Original Issue (RESOLVED)

**Date:** February 10, 2026  
**Environment:** Production (Hetzner VPS)  
**Issue:** Spread Bot failing with `1401 Unauthorized` on balance fetch, despite signature fix working for Volume Bot

---

## What We've Fixed

1. **JSON Signature Fix Applied:**
   - Removed `separators=(',', ':')` from `json.dumps()` calls in `app/coinstore_connector.py`
   - Changed to default `json.dumps(params)` (with spaces) as per Coinstore API requirements
   - **This fix works for Volume Bot** - Volume Bot successfully trades with Coinstore

2. **Spread Bot Order Size Fix:**
   - Updated `app/spread_bot.py` to use `order_size_usd` config (defaults to $10)
   - Converts USD to base tokens correctly:
     - Bid (BUY): `$10 USDT / bid_price` = SHARP tokens to buy
     - Ask (SELL): `$10 USDT / ask_price` = SHARP tokens to sell
   - Code deployed: commit `b2d69f2`

---

## Current Problem

**Spread Bot is getting `1401` application-level error** when calling `fetch_balance()`:

**IMPORTANT:** `1401` is NOT an HTTP status code - it's a Coinstore application-level error code. If HTTP status is `200` with `{"code": 1401}`, that means:
- ✅ **Authentication/signature passed** (HTTP 200 OK)
- ❌ **Application-level error** (could be wrong endpoint, missing params, account permissions, etc.)

**Current Error Logs:**
```
{"timestamp": "2026-02-10T19:04:42.214607", "level": "info", "logger": "app.coinstore_adapter", "message": "💰 Coinstore balance API response: code=1401, data type=<class 'NoneType'>"}
{"timestamp": "2026-02-10T19:04:42.214741", "level": "error", "logger": "app.coinstore_adapter", "message": "Coinstore API error: code=1401, msg=Unauthorized, full response={'message': 'Unauthorized', 'code': 1401}"}
```

**⚠️ MISSING CRITICAL INFO:**
- **HTTP Status Code:** Not logged (need to verify if it's 200 or 401)
- **Full Request Details:** Headers, payload, exact endpoint URL
- **Raw Response Body:** Full JSON response

**Key Observations:**
- Volume Bot uses the **same connector** (`CoinstoreConnector`) and **works perfectly**
- Spread Bot uses the **same initialization code** (`create_coinstore_exchange`) as Volume Bot
- Both bots use the **same API credentials** (from `exchange_credentials` table)
- The signature fix is deployed and working for Volume Bot
- Spread Bot fails on the **first API call** (`get_balances()` → `/spot/accountList`)

---

## Code Flow Comparison

### Volume Bot (Working):
```python
# app/bot_runner.py → CEXVolumeBot
exchange = await create_coinstore_exchange(api_key, api_secret, proxy_url)
balance = await exchange.fetch_balance()  # ✅ WORKS
```

### Spread Bot (Failing):
```python
# app/bot_runner.py → SpreadBot
exchange = await create_coinstore_exchange(api_key, api_secret, proxy_url)
balance = await exchange.fetch_balance()  # ❌ 1401 Unauthorized
```

**Both use identical initialization and same connector code.**

---

## Technical Details

### Balance API Call:
- **Endpoint:** `POST /spot/accountList`
- **Payload:** `{}` (empty JSON object)
- **Signature generation:** Uses `json.dumps({})` = `'{}'` (default format, with spaces)
- **Headers:** `X-CS-APIKEY`, `X-CS-SIGN`, `X-CS-EXPIRES`

### Connector Code (app/coinstore_connector.py):
```python
# Line 119 - POST requests
payload = json.dumps(params) if params else json.dumps({})  # Default format (no separators)

# Line 256-259 - get_balances()
async def get_balances(self) -> Dict[str, Any]:
    endpoint = "/spot/accountList"
    return await self._request('POST', endpoint, params={}, authenticated=True)
```

---

## Questions for Developer

1. **Why would the same connector code work for Volume Bot but fail for Spread Bot?**
   - Both use `create_coinstore_exchange()` with same credentials
   - Both call `fetch_balance()` → `get_balances()` → same endpoint
   - Same signature generation code path

2. **Could there be a timing/caching issue?**
   - Spread Bot starts immediately after app restart
   - Volume Bot works on same cycle
   - Could there be a race condition or instance caching?

3. **Is there a difference in how the adapter wraps the connector?**
   - `CoinstoreAdapter.fetch_balance()` calls `connector.get_balances()`
   - Volume Bot uses `CoinstoreAdapter` via `create_coinstore_exchange()`
   - Spread Bot also uses `CoinstoreAdapter` via `create_coinstore_exchange()`

4. **Should we check the exact signature being generated?**
   - Volume Bot logs show successful balance fetch
   - Spread Bot logs show 1401 error
   - Should we add detailed signature logging to compare?

5. **Could it be related to how Spread Bot is initialized vs Volume Bot?**
   - Spread Bot runs in `_run_spread_bot()` task
   - Volume Bot runs in `_run_cex_volume_bot()` task
   - Both create exchange instances independently

---

## Requested Help

**Please help us understand:**
1. Why the same connector code fails for Spread Bot but works for Volume Bot
2. What we should check/debug to identify the root cause
3. Any known issues with Coinstore API when multiple bots use the same credentials

**We're ready to:**
- Add detailed logging
- Test specific scenarios
- Make code changes as needed

---

## Environment

- **Server:** Hetzner VPS (5.161.64.209)
- **Python:** 3.12
- **App:** FastAPI with uvicorn
- **Database:** Railway PostgreSQL
- **Latest commit:** `b2d69f2` (Spread Bot order_size_usd fix)

---

## Logs Location

Production logs: `/opt/trading-bridge/app.log` on Hetzner server

---

**Status:** 🔴 **BLOCKED** - Spread Bot cannot fetch balance, preventing order placement
