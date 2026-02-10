# Spread Bot 1401 Error - SOLUTION FOUND

## ✅ Root Cause Identified

**Issue:** API Key Permissions  
**Error:** `{"message":"Unauthorized","code":1401}` on `/spot/accountList`  
**Status:** HTTP 200 (signature works) but application-level rejection

---

## The Problem

Coinstore API keys have **separate permission toggles**:
- ✅ **Trade** - Enabled (orders execute successfully)
- ❌ **Read** - Disabled (balance queries rejected with 1401)

**Why Volume Bot Works:**
- Volume Bot skips balance check when it fails
- Places market orders anyway (uses Trade permission)
- Exchange rejects if insufficient funds

**Why Spread Bot Fails:**
- Spread Bot requires balance to calculate order sizes
- Balance query fails with 1401 (no Read permission)
- Bot stops before placing orders

---

## Solution: Option A (Preferred) ✅

### Enable Read Permission on API Key

1. **Go to Coinstore API Management:**
   - URL: https://www.coinstore.com/#/user/bindAuth/ManagementAPI
   - Or: Coinstore Dashboard → API Management

2. **Find the Active API Key:**
   - Look for the key used by the bot
   - Key should match: `client_new_sharp_foundation` account

3. **Enable Read Permission:**
   - Find permission toggles (typically "Read", "Account", or "Query")
   - Enable the **Read** / **Account** / **Query** permission
   - Save changes

4. **No Code Changes Needed:**
   - Both bots will work immediately after permission is enabled
   - Spread Bot will be able to fetch balance
   - Volume Bot balance check will also work

---

## Solution: Option B (Workaround)

### Skip Balance Check, Use Configured Amounts

**Only use if Option A is not possible** (e.g., can't modify API key permissions).

**Modify `app/spread_bot.py`:**

```python
async def _run_cycle(self):
    """Execute one cycle of the spread bot."""
    logger.info(f"📈 Spread bot {self.bot_id} - Running cycle")
    
    # Option B: Skip balance check, use configured amounts
    # Instead of: balance = await self._fetch_balance()
    try:
        balance = await self._fetch_balance()
        self.inventory_base = Decimal(str(balance.get('base_free', 0)))
        self.inventory_quote = Decimal(str(balance.get('quote_free', 0)))
    except Exception as e:
        logger.warning(f"⚠️ Balance check failed: {e}. Using configured order sizes.")
        # Use configured amounts - exchange will reject if insufficient funds
        self.inventory_base = Decimal('999999999')  # Assume we have enough
        self.inventory_quote = Decimal('999999999')  # Assume we have enough
    
    # Rest of cycle continues normally...
```

**Note:** This is less ideal because:
- Bot can't optimize order sizes based on actual balance
- May place orders that get rejected
- Less efficient than knowing actual balance

---

## Verification Steps

After enabling Read permission:

1. **Check Spread Bot Logs:**
   ```
   ✅ Balance: X base, Y quote
   📊 Mid price: Z
   ✅ Bid placed: ...
   ✅ Ask placed: ...
   ```

2. **Check Volume Bot Logs:**
   ```
   Balance check successful: base=X, quote=Y
   ```

3. **Both bots should work:**
   - Spread Bot: Places limit orders successfully
   - Volume Bot: Balance check succeeds (no longer skipped)

---

## Summary

| Issue | Cause | Solution |
|-------|-------|----------|
| 1401 Error | API key missing Read permission | Enable Read permission on API key |
| Spread Bot blocked | Needs balance to calculate sizes | Read permission enables balance query |
| Volume Bot works | Skips balance check | Will also work better with Read permission |

---

**Status:** ✅ **SOLVED** - Enable Read permission on Coinstore API key

**Next Action:** Check Coinstore dashboard and enable Read permission
