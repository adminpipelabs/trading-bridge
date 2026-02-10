# Spread Bot LIMIT Order 1401 Error - Help Request

**Date:** February 10, 2026  
**Status:** ❌ **BLOCKED** - LIMIT orders fail with 1401, MARKET orders work  
**Urgency:** HIGH - Spread bot deployment blocked

---

## 🔴 **The Problem**

**LIMIT orders fail with 1401 Unauthorized, but MARKET orders work fine.**

### Test Results

**✅ MARKET Orders:** Work perfectly
```json
Payload: {"symbol": "SHARPUSDT", "side": "BUY", "ordType": "MARKET", "timestamp": 1770752545990, "ordAmt": "10.0"}
Response: ✅ Success (order executes)
```

**❌ LIMIT Orders:** Fail with 1401
```json
Payload: {"symbol": "SHARPUSDT", "side": "BUY", "ordType": "LIMIT", "timestamp": 1770752231299, "ordQty": "100.0", "ordPrice": "0.0068096"}
Response: {"message":"Unauthorized","code":1401}
```

**HTTP Status:** 200 (authentication passed)  
**Application Error Code:** 1401 (Unauthorized)

---

## 📋 **What We've Tried**

1. ✅ **Parameter name fix:** Changed `price` → `ordPrice` (per Coinstore docs)
2. ✅ **Signature verification:** HTTP 200 confirms signature works
3. ✅ **JSON format:** Using default `json.dumps()` (with spaces) - same as MARKET orders
4. ✅ **Timestamp:** Included in payload, matches `X-CS-EXPIRES` header
5. ✅ **Order structure:** Matches Coinstore docs example

**Current LIMIT order payload:**
```python
{
    'symbol': 'SHARPUSDT',
    'side': 'BUY',  # or 'SELL'
    'ordType': 'LIMIT',
    'timestamp': 1770752231299,  # milliseconds
    'ordQty': '100.0',  # base currency amount
    'ordPrice': '0.0068096'  # limit price
}
```

---

## 🔍 **Key Observations**

1. **MARKET orders work** → Signature/auth is correct
2. **HTTP 200** → Authentication passed
3. **1401 error** → Application-level rejection (not signature)
4. **Same API key** → Used for both MARKET and LIMIT orders
5. **Same endpoint** → `/trade/order/place` for both

**Possible causes:**
- ❓ API key permission issue (but MARKET orders work?)
- ❓ Missing required parameter for LIMIT orders
- ❓ Parameter format/type issue (`ordPrice` vs `price`?)
- ❓ Account-level restriction on LIMIT orders
- ❓ Coinstore API bug/inconsistency

---

## 📚 **Open Source Spread Bot References**

As suggested, there are many open source spread bots on GitHub. Key examples:

1. **Adamant CoinOptimus** (mentioned earlier)
   - https://github.com/Adamant-im/adamant-coinoptimus
   - Supports Coinstore
   - Uses LIMIT orders for spread trading

2. **Hummingbot** (popular market making framework)
   - https://github.com/hummingbot/hummingbot
   - Multiple exchange connectors including Coinstore
   - Extensive LIMIT order implementation

3. **CCXT Library** (exchange connector library)
   - https://github.com/ccxt/ccxt
   - Standardized LIMIT order interface
   - Coinstore integration

---

## 🎯 **Questions for Dev**

1. **Parameter Names:**
   - Is `ordPrice` correct, or should it be `price`?
   - Are there any other required parameters for LIMIT orders?

2. **API Key Permissions:**
   - Do LIMIT orders require different permissions than MARKET orders?
   - Should we check specific permission flags?

3. **Order Format:**
   - Is the payload structure correct?
   - Should `ordQty` and `ordPrice` be strings or numbers?

4. **Coinstore-Specific:**
   - Are there any Coinstore-specific requirements for LIMIT orders?
   - Any known issues with LIMIT orders on Coinstore?

5. **Open Source Examples:**
   - Can you point to a working Coinstore LIMIT order implementation?
   - Any specific GitHub repos we should reference?

---

## 💻 **Current Code**

**File:** `app/coinstore_connector.py` (lines 345-350)

```python
else:
    # LIMIT orders: use quantity and price
    # Per Coinstore docs: use ordQty and ordPrice (not 'price')
    params['ordQty'] = str(amount)
    if price:
        params['ordPrice'] = str(price)  # Coinstore uses 'ordPrice' not 'price'
```

**File:** `app/spread_bot.py` (line 275)

```python
order = await self.exchange.create_limit_order(
    symbol=self.symbol,
    side=side,
    amount=float(amount),
    price=float(price)
)
```

---

## 🚀 **What We Need**

**Goal:** Get LIMIT orders working so Spread Bot can deploy.

**Spread Bot Requirements:**
- ✅ Fetch ticker (works)
- ❌ Place LIMIT buy order (fails with 1401)
- ❌ Place LIMIT sell order (fails with 1401)
- ❓ Check open orders (not tested yet)
- ❓ Cancel orders (not tested yet)

**Deployment Plan:**
- Deploy as new bot type (`spread`)
- Start with $5-10 on SHARP/USDT
- Small spread (0.3%)
- Monitor first few cycles

---

## 📝 **Next Steps**

1. **Wait for Dev guidance** on LIMIT order parameters/permissions
2. **Check open source examples** (Adamant CoinOptimus, Hummingbot)
3. **Test with working implementation** once we have correct parameters
4. **Deploy Spread Bot** once LIMIT orders work

---

**Status:** ⏸️ **WAITING FOR DEV INPUT**

Please review and provide guidance on:
- Correct LIMIT order parameters for Coinstore
- Any permission/account requirements
- Reference to working open source implementation
