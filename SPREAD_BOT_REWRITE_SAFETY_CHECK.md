# Spread Bot Rewrite - Production Safety Check

## Changes Made

**File:** `app/spread_bot.py` - Complete rewrite to match developer spec

## Backward Compatibility ✅

### Config Field Support

**Old Format (still supported):**
```json
{
  "spread_bps": 200,        // 2% spread (200 basis points)
  "order_size": 1000,       // Old format (treated as USD if < 100)
  "refresh_interval": 30    // Seconds
}
```

**New Format (developer spec):**
```json
{
  "spread_percent": 0.3,              // 0.3% spread
  "order_size_usdt": 10,              // $10 USD per side
  "poll_interval_seconds": 5,         // Check fills every 5s
  "refresh_interval_seconds": 60      // Refresh orders every 60s
}
```

**Auto-conversion:**
- `spread_bps: 200` → `spread_percent: 2.0%` (converted automatically)
- `spread_bps: 30` → `spread_percent: 0.3%` (converted automatically)
- Old `order_size` values > 100 → defaults to $10 USD (safe fallback)

### API Compatibility ✅

**No breaking changes:**
- Still uses `exchange.create_limit_order()` (same interface)
- Still uses `exchange.fetch_open_orders()` (same interface)
- Still uses `exchange.cancel_order()` (same interface)
- Still uses `exchange.fetch_ticker()` (same interface)

### Database Compatibility ✅

**Trade logging:**
- Still writes to `trade_logs` table (same schema)
- Same fields: `bot_id`, `side`, `amount`, `price`, `cost_usd`, `order_id`

### Frontend Compatibility ✅

**No frontend changes needed:**
- Bot still exposes same status via `/bots/{bot_id}/stats`
- Bot still exposes same balance/volume via `/bots/{bot_id}/balance-and-volume`
- Bot still uses same `bot_type: "spread"` field

## Potential Issues & Mitigations

### 1. Config Field Mismatch ⚠️

**Issue:** `bot_runner.py` sets defaults with old field names (`spread_bps`, `order_size`)

**Fix Applied:** ✅ Added backward compatibility in `spread_bot.py` to handle both formats

**Status:** Safe - old bots will continue working

### 2. fetch_open_orders Response Format ⚠️

**Issue:** Need to verify Coinstore returns orders in expected format

**Fix Applied:** ✅ Added robust parsing for both list and dict formats

**Status:** Safe - handles multiple response formats

### 3. Missing Balance Check ⚠️

**Issue:** New code doesn't check balance before placing orders

**By Design:** ✅ Per developer spec - uses configured size, exchange rejects if insufficient

**Status:** Safe - same approach as Volume Bot

### 4. Infinite Loop Risk ⚠️

**Issue:** Inner monitoring loop could run forever if orders never fill

**Fix Applied:** ✅ Added `refresh_interval` check to break loop after 60s

**Status:** Safe - loop breaks and restarts cycle

## Testing Checklist

Before deploying to production:

- [ ] Test with existing bot config (old format)
- [ ] Test with new bot config (new format)
- [ ] Verify orders place correctly
- [ ] Verify fill detection works
- [ ] Verify order cancellation works
- [ ] Verify trade logging works
- [ ] Check logs for errors

## Rollback Plan

If issues occur:

1. **Quick fix:** Revert `app/spread_bot.py` to previous version
2. **Config fix:** Update `bot_runner.py` defaults if needed
3. **No database changes:** No schema changes, safe to rollback

## Risk Assessment

**Risk Level:** 🟡 **MEDIUM**

**Reasons:**
- Complete rewrite of core logic
- New fill monitoring loop (untested in production)
- Config format changes (mitigated with backward compatibility)

**Mitigations:**
- ✅ Backward compatible config parsing
- ✅ Robust error handling
- ✅ Safe defaults
- ✅ No database schema changes
- ✅ No frontend changes needed

**Recommendation:** 
- Test on staging/dev first if possible
- Monitor logs closely after deployment
- Have rollback ready

---

**Status:** ✅ Code is backward compatible, but should be tested before production deployment
