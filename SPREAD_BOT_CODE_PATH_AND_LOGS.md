# Spread Bot Code Path and Error Logs - Developer Analysis

## ✅ Critical Finding: HTTP 200 with Code 1401

**HTTP Status: 200** - Authentication/signature **PASSED**  
**Application Error Code: 1401** - Coinstore application-level rejection

```
{"timestamp": "2026-02-10T19:16:04.391303", "level": "info", "logger": "app.coinstore_connector", "message": "🔵 Coinstore API POST /spot/accountList - HTTP Status: 200, Response length: 38"}
{"timestamp": "2026-02-10T19:16:04.391447", "level": "info", "logger": "app.coinstore_connector", "message": "🔵 Full response body: {\"message\":\"Unauthorized\",\"code\":1401}"}
{"timestamp": "2026-02-10T19:16:04.391731", "level": "error", "logger": "app.coinstore_connector", "message": "   HTTP Status: 200 (authentication passed)"}
{"timestamp": "2026-02-10T19:16:04.392006", "level": "error", "logger": "app.coinstore_connector", "message": "   Full response: {'message': 'Unauthorized', 'code': 1401}"}
```

**Conclusion:** This is NOT a signature/auth issue. The signature is correct, but Coinstore is rejecting the request at the application level.

---

## Code Path Analysis

### 1. Spread Bot Initialization (`app/bot_runner.py`)

**Location:** `app/bot_runner.py`, lines 1251-1408

**Flow:**
```python
async def _run_spread_bot(self, bot_id: str):
    # ... get bot config from database ...
    
    # Create exchange instance (SAME as Volume Bot)
    if exchange_name == "coinstore":
        from app.coinstore_adapter import create_coinstore_exchange
        exchange = await create_coinstore_exchange(
            api_key=api_key,
            api_secret=api_secret,
            proxy_url=proxy_url
        )
    
    # Create SpreadBot instance
    spread_bot = SpreadBot(
        bot_id=bot_id,
        exchange=exchange,  # CoinstoreAdapter instance
        symbol=symbol,       # "SHARP/USDT"
        config=config,
        db_session=db
    )
    
    await spread_bot.start()  # Runs main loop
```

**Key Point:** Uses **exact same** `create_coinstore_exchange()` as Volume Bot.

---

### 2. Spread Bot Main Loop (`app/spread_bot.py`)

**Location:** `app/spread_bot.py`, lines 77-136

**Cycle Flow:**
```python
async def _run_cycle(self):
    # Step 1: Fetch balance
    balance = await self._fetch_balance()  # ❌ FAILS HERE with 1401
    
    # Step 2: Fetch orderbook and calculate mid price
    mid_price = await self._get_mid_price()  # Uses fetch_order_book()
    
    # Step 3-6: Calculate prices, cancel stale orders, place new orders
    # ...
```

---

### 3. Balance Fetch (`app/spread_bot.py`)

**Location:** `app/spread_bot.py`, lines 138-175

**Code:**
```python
async def _fetch_balance(self) -> Optional[dict]:
    try:
        # BitMart requires type parameter
        if hasattr(self.exchange, 'id') and self.exchange.id == 'bitmart':
            balance = await self.exchange.fetch_balance({'type': 'spot'})
        else:
            balance = await self.exchange.fetch_balance()  # ❌ FAILS HERE
        
        # Parse and return balance...
    except Exception as e:
        logger.error(f"❌ Balance fetch error: {e}", exc_info=True)
        return None
```

**Calls:** `exchange.fetch_balance()` where `exchange` is a `CoinstoreAdapter` instance.

---

### 4. CoinstoreAdapter.fetch_balance() (`app/coinstore_adapter.py`)

**Location:** `app/coinstore_adapter.py`, lines 121-192

**Code:**
```python
async def fetch_balance(self, params: Optional[Dict] = None) -> Dict[str, Any]:
    try:
        data = await self.connector.get_balances()  # Calls connector
        
        code = data.get('code')
        if code == 0 or code == "0":
            # Parse and return balance...
        else:
            # ❌ ERROR HANDLING - Gets 1401 here
            error_code = data.get('code')
            error_msg = data.get('msg') or data.get('message')
            raise Exception(f"Coinstore API error (code {error_code}): {error_msg}")
```

**Calls:** `self.connector.get_balances()` where `connector` is `CoinstoreConnector`.

---

### 5. CoinstoreConnector.get_balances() (`app/coinstore_connector.py`)

**Location:** `app/coinstore_connector.py`, lines 256-259

**Code:**
```python
async def get_balances(self) -> Dict[str, Any]:
    """Get account balances."""
    endpoint = "/spot/accountList"
    return await self._request('POST', endpoint, params={}, authenticated=True)
```

**Request Details:**
- **Method:** `POST`
- **Endpoint:** `/spot/accountList`
- **Payload:** `{}` (empty JSON object)
- **Authenticated:** `True` (includes signature headers)

---

### 6. Price Fetching (`app/spread_bot.py`)

**Location:** `app/spread_bot.py`, lines 177-196

**Code:**
```python
async def _get_mid_price(self) -> Optional[Decimal]:
    """Fetch orderbook and calculate mid price."""
    try:
        orderbook = await self.exchange.fetch_order_book(self.symbol, limit=5)
        
        if not orderbook.get('bids') or not orderbook.get('asks'):
            return None
        
        best_bid = Decimal(str(orderbook['bids'][0][0]))
        best_ask = Decimal(str(orderbook['asks'][0][0]))
        mid_price = (best_bid + best_ask) / 2
        
        return mid_price
    except Exception as e:
        logger.error(f"❌ Orderbook fetch error: {e}", exc_info=True)
        return None
```

**Note:** This uses `fetch_order_book()` which should be a **PUBLIC** endpoint (no auth needed). The error happens **before** this step, so we never see if orderbook fetch works.

---

## Comparison: Volume Bot vs Spread Bot

### Volume Bot (Working):
```python
# app/bot_runner.py → _run_cex_volume_bot()
exchange = await create_coinstore_exchange(api_key, api_secret, proxy_url)
# ... later ...
balance = await exchange.fetch_balance()  # ✅ WORKS
```

### Spread Bot (Failing):
```python
# app/bot_runner.py → _run_spread_bot()
exchange = await create_coinstore_exchange(api_key, api_secret, proxy_url)  # SAME
# ... later ...
balance = await exchange.fetch_balance()  # ❌ HTTP 200 + code 1401
```

**Both use identical code path up to the balance fetch.**

---

## Developer's Questions Answered

### Check 1: Is the spread bot actually calling the Coinstore connector?
**✅ YES** - Same code path as Volume Bot:
- `_run_spread_bot()` → `create_coinstore_exchange()` → `CoinstoreAdapter` → `CoinstoreConnector`

### Check 2: Is it using LIMIT order params correctly?
**⚠️ NOT RELEVANT YET** - The bot fails **before** placing orders (fails on balance fetch).

### Check 3: Is it fetching price correctly?
**✅ YES** - Uses `fetch_order_book()` (public endpoint), but **never reaches this step** because balance fetch fails first.

---

## The Real Issue

**HTTP 200 + Code 1401** means:
- ✅ Signature generation is correct
- ✅ Authentication headers are correct
- ✅ Request reaches Coinstore API
- ❌ Coinstore rejects at application level

**Possible Causes:**
1. **Wrong endpoint?** `/spot/accountList` might not be the correct endpoint for balance
2. **Missing required params?** Empty `{}` payload might need additional fields
3. **Account permissions?** API key might not have "Read" permission enabled
4. **Account status?** Account might be restricted or suspended
5. **Different API version?** Endpoint might have changed or require different format

---

## What to Check Next

1. **Compare Volume Bot's successful balance call:**
   - Does Volume Bot use the same endpoint?
   - Does Volume Bot send the same payload?
   - Are there any differences in headers or request format?

2. **Check Coinstore API docs:**
   - Verify `/spot/accountList` is the correct endpoint
   - Check if it requires any additional parameters
   - Verify API key permissions needed

3. **Add request logging:**
   - Log exact headers sent (X-CS-APIKEY, X-CS-SIGN, X-CS-EXPIRES)
   - Log exact payload bytes
   - Compare with Volume Bot's successful request

---

## Files Referenced

- **Spread Bot Code:** `app/spread_bot.py` (337 lines)
- **Bot Runner:** `app/bot_runner.py` (lines 1251-1408)
- **Coinstore Adapter:** `app/coinstore_adapter.py` (lines 121-192)
- **Coinstore Connector:** `app/coinstore_connector.py` (lines 256-259, 189-230)

---

**Status:** 🔴 **BLOCKED** - HTTP 200 confirms auth works, but application-level 1401 error prevents balance fetch
