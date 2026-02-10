# Spread Bot Code Path Analysis - Answers to Dev Questions

**Date:** February 10, 2026  
**Purpose:** Compare spread bot vs volume bot code paths to find why LIMIT orders fail

---

## ✅ **Answers to Dev's Questions**

### 1. **Does the spread bot use the same connector file as the volume bot?**

**YES** - Both use the same connector:
- **Volume Bot:** `app/cex_volume_bot.py` → `app/coinstore_adapter.py` → `app/coinstore_connector.py`
- **Spread Bot:** `app/spread_bot.py` → `app/coinstore_adapter.py` → `app/coinstore_connector.py`

**Code Path:**
```python
# Volume Bot (cex_volume_bot.py:618)
order = await self.exchange.create_market_buy_order(...)
  → coinstore_adapter.py:create_market_buy_order()
    → coinstore_connector.py:place_order(order_type='market')

# Spread Bot (spread_bot.py:275)
order = await self.exchange.create_limit_order(...)
  → coinstore_adapter.py:create_limit_order()
    → coinstore_connector.py:place_order(order_type='limit')
```

---

### 2. **Does the spread bot build the payload in the same function as the volume bot?**

**YES** - Both build payload in the same function: `coinstore_connector.py:place_order()`

**Same function, different branches:**
```python
# app/coinstore_connector.py:place_order()
if order_type.lower() == 'market':
    # MARKET order payload (works)
    params['timestamp'] = timestamp_ms
    params['ordAmt'] = str(amount)  # or ordQty
else:
    # LIMIT order payload (fails with 1401)
    params['timestamp'] = timestamp_ms  # ✅ Now included
    params['ordPrice'] = float(price)   # ✅ Now number
    params['ordQty'] = f"{amount:.2f}"  # ✅ String
```

---

### 3. **Print the exact payload and headers the spread bot sends**

**DEBUG LOGGING ADDED** - Added logging right before `session.post()` call:

**Location:** `app/coinstore_connector.py:189` (right before HTTP request)

**Logs:**
```python
logger.info("=" * 80)
logger.info("🔍 DEBUG: EXACT REQUEST BEING SENT (right before HTTP call)")
logger.info("=" * 80)
logger.info(f"URL: {url}")
logger.info(f"Method: POST")
logger.info(f"Payload (string): {payload}")
logger.info(f"Payload (bytes): {body_bytes}")
logger.info(f"Payload length: {len(body_bytes)} bytes")
logger.info(f"Headers: {headers}")
logger.info(f"Request kwargs: {request_kwargs}")
logger.info("=" * 80)
```

**To see the logs:**
```bash
# On Hetzner
tail -f /opt/trading-bridge/app.log | grep -A 10 "DEBUG: EXACT REQUEST"
```

---

### 4. **Is the spread bot hitting `/api/trade/order/place` or a different endpoint?**

**SAME ENDPOINT** - Both use `/trade/order/place`

**Code:** `app/coinstore_connector.py:311`
```python
endpoint = "/trade/order/place"
```

---

### 5. **Is the spread bot running through any middleware, wrapper, or base class?**

**NO MIDDLEWARE** - Both go directly through:
1. `coinstore_adapter.py` (thin wrapper, just passes through)
2. `coinstore_connector.py:place_order()` (builds payload)
3. `coinstore_connector.py:_request()` (sends HTTP request)

**No base classes, no middleware, no request modification.**

---

## 🔍 **Key Differences Found**

### **Payload Building (Same Function, Different Branch):**

**MARKET Orders (Works):**
```python
params = {
    'symbol': 'SHARPUSDT',
    'side': 'BUY',
    'ordType': 'MARKET',
    'timestamp': 1770756788798,
    'ordAmt': '10.0'  # or 'ordQty': '1394.50'
}
```

**LIMIT Orders (Fails):**
```python
params = {
    'symbol': 'SHARPUSDT',
    'side': 'BUY',
    'ordType': 'LIMIT',
    'timestamp': 1770756788798,  # ✅ Now included
    'ordPrice': 0.005746,         # ✅ Now number (float)
    'ordQty': '1740.34'           # ✅ String
}
```

---

## 📋 **Next Steps**

1. **Run spread bot** and capture the debug logs showing exact payload/headers
2. **Compare** with working MARKET order logs
3. **Check** if payload JSON serialization differs between MARKET and LIMIT
4. **Verify** headers are identical (especially signature calculation)

---

## 🎯 **Hypothesis**

Since both use the same connector, same endpoint, same function, the issue must be:
- **Payload JSON serialization** (how `json.dumps()` handles float vs string)
- **Signature calculation** (if payload string differs, signature differs)
- **Something in the LIMIT-specific payload** that Coinstore rejects

**The debug logs will show us the exact difference.**
