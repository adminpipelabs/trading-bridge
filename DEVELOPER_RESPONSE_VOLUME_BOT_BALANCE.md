# Developer Questions Answered - Volume Bot Balance Check

## Critical Finding: Volume Bot ALSO Fails on `/spot/accountList`

**Answer to Developer's Question:** Volume Bot **DOES call** `/spot/accountList`, but it **SKIPS the error** and continues trading anyway.

---

## Evidence from Logs

### Volume Bot Balance Call (FAILS):
```
{"timestamp": "2026-02-10T19:19:23.653158", "level": "info", "logger": "app.coinstore_connector", "message": "🔵 Coinstore API POST /spot/accountList - HTTP Status: 200, Response length: 41"}
{"timestamp": "2026-02-10T19:19:23.653890", "level": "error", "logger": "app.coinstore_connector", "message": "Coinstore API request failed for /spot/accountList: Invalid JSON response: {\"message\":\"signature-failed\",\"code\":401}"}
{"timestamp": "2026-02-10T19:19:23.655314", "level": "error", "logger": "cex_volume_bot", "message": "❌ Error fetching balance from coinstore: Invalid JSON response: {\"message\":\"signature-failed\",\"code\":401}"}
```

### Spread Bot Balance Call (FAILS):
```
{"timestamp": "2026-02-10T19:16:04.391303", "level": "info", "logger": "app.coinstore_connector", "message": "🔵 Coinstore API POST /spot/accountList - HTTP Status: 200, Response length: 38"}
{"timestamp": "2026-02-10T19:16:04.391447", "level": "info", "logger": "app.coinstore_connector", "message": "🔵 Full response body: {\"message\":\"Unauthorized\",\"code\":1401}"}
```

**Both bots get errors on `/spot/accountList` endpoint!**

---

## Volume Bot Code: Skips Balance Check

**Location:** `app/cex_volume_bot.py`, lines 699-712

```python
# SKIP BALANCE CHECK - Try to place order directly
# If balance check fails but credentials are valid, we can still try trading
# The exchange will reject with InsufficientFunds if needed
base_balance = None
quote_balance = None
try:
    base_balance, quote_balance = await self.get_balances()
    logger.info(f"Balance check successful: base={base_balance}, quote={quote_balance}")
except Exception as balance_error:
    logger.warning(f"⚠️  Balance check failed: {balance_error}. Skipping balance check and trying direct trade.")
    logger.info(f"This is OK - we'll try placing order and exchange will reject if insufficient funds")
    # Set default balances to allow trade attempt
    base_balance = 0.0
    quote_balance = 0.0
```

**Volume Bot Strategy:**
1. Try to fetch balance
2. If it fails → **Catch error and continue**
3. Place market order anyway (exchange will reject if insufficient funds)

**Spread Bot Strategy:**
1. Try to fetch balance
2. If it fails → **STOP** (can't calculate order sizes without balance)
3. Skip cycle

---

## Full JSON Response Bodies

### Volume Bot Error (code 401):
```json
{"message":"signature-failed","code":401}
```

### Spread Bot Error (code 1401):
```json
{"message":"Unauthorized","code":1401}
```

**Note:** Both are HTTP 200 responses with application-level error codes.

---

## Developer's Hypothesis: CONFIRMED ✅

> "My bet: the spread bot calls `get_balances()` before placing orders (to calculate how many limit orders it can afford), while the volume bot just fires market orders without checking balance first."

**CORRECT:**
- ✅ Volume Bot calls balance but **skips** when it fails
- ✅ Spread Bot **requires** balance to work
- ✅ Both get errors on `/spot/accountList`
- ✅ Volume Bot works because it doesn't need balance (market orders)
- ✅ Spread Bot fails because it needs balance (limit orders require size calculation)

---

## The Real Issue

**The `/spot/accountList` endpoint is failing for BOTH bots**, but:
- Volume Bot doesn't care (skips balance check)
- Spread Bot is blocked (needs balance)

**This means:**
- The issue is **NOT** spread bot vs volume bot logic
- The issue is **specifically** the `/spot/accountList` endpoint
- Could be:
  - Wrong endpoint URL
  - Missing required parameters
  - Account permissions
  - API key restrictions

---

## Next Steps

1. **Check Coinstore API docs** for correct balance endpoint
2. **Compare with working order placement** - Volume Bot places orders successfully, so order endpoints work
3. **Check if balance endpoint requires different params** - Maybe it needs account type or other fields

---

## Full Response Logging Added

I've added the developer's requested logging:
```python
logger.error(f"   FULL JSON RESPONSE BODY: {response_text}")  # Developer requested
```

This will capture the complete response body for the next error.

---

**Status:** ✅ **CONFIRMED** - Volume Bot skips balance check, Spread Bot requires it. Both fail on `/spot/accountList`.
