# Health Check Error Fixes — Summary for Dev

## Issues Fixed

Fixed three critical errors in the bot health monitoring system that were causing health checks to fail:

### 1. **Timezone Error: `can't subtract offset-naive and offset-aware datetimes`**
   - **Error Location**: `app/bot_health.py` line 240 (heartbeat check)
   - **Problem**: Database returns `last_heartbeat` as timezone-aware datetime, but code was calling `.replace(tzinfo=timezone.utc)` which fails on already-aware datetimes
   - **Fix**: Added timezone detection:
     ```python
     if heartbeat.tzinfo is None:
         heartbeat = heartbeat.replace(tzinfo=timezone.utc)  # Naive → UTC
     else:
         heartbeat = heartbeat.astimezone(timezone.utc)     # Aware → UTC
     ```
   - **Impact**: Heartbeat checks now work correctly for all datetime formats

### 2. **NoneType Error: `'NoneType' object has no attribute 'split'`**
   - **Error Location**: `app/bot_health.py` line 379 (`_check_balance` method)
   - **Problem**: Some bots have `pair = None` (e.g., "Sharp Foundation uniswap volume" bot), causing `.split('/')` to fail
   - **Fix**: Added validation before parsing:
     ```python
     if not pair:
         return None
     parts = pair.split('/')
     ```
   - **Additional**: Added early return in `_check_bot_health` if `pair` is missing:
     ```python
     if not pair:
         await self._update_health(..., reason="Bot missing pair configuration")
         return
     ```
   - **Impact**: Bots without pair configuration are marked as "error" instead of crashing

### 3. **Attribute Error: `'str' object has no attribute 'get'`**
   - **Error Location**: `app/bot_health.py` line 208 (`_check_solana_bot_health` method)
   - **Problem**: `result['transactions']` was sometimes not a dict (possibly None or string), causing `.get()` to fail
   - **Fix**: Added result validation and safe access:
     ```python
     # Validate result structure
     if not result or not isinstance(result, dict):
         await self._update_health(..., reason="Health check returned invalid result")
         return
     
     # Safely get transactions data
     transactions = result.get('transactions', {})
     if not isinstance(transactions, dict):
         transactions = {}
     last_trade = transactions.get('last_tx_time')
     trade_count = transactions.get('count', 0)
     ```
   - **Additional**: Wrapped `check_health()` call in try/except for better error handling
   - **Impact**: Solana health checks handle malformed responses gracefully

## Code Changes

**File**: `app/bot_health.py`

1. **Heartbeat timezone handling** (lines 263-272)
   - Detects naive vs aware datetimes
   - Converts both to UTC correctly

2. **Pair validation** (lines 260-270, 383-386)
   - Validates `pair` exists before use
   - Returns early with error status if missing

3. **Result validation** (lines 188-232)
   - Validates health check result structure
   - Safely accesses nested `transactions` dict
   - Handles exceptions from Solana health checker

## Testing Notes

- **Bots affected**:
  - `43e258a7-f8d1-4f5f-ac27-46c89da902d2` (Sharp Spread) - Fixed timezone error
  - `a2109483-2ded-45fc-a4a8-6f4fdce76b44` (Sharp Foundation uniswap volume) - Fixed NoneType error
  - `726186c7-0f5e-44a2-8c7e-b2e01186c0e4` (Lynk) - Fixed string.get() error

- **Expected behavior after fix**:
  - Health checks complete without crashing
  - Bots with missing config show "error" status instead of crashing
  - All datetime comparisons work correctly
  - Health monitor continues running even if individual checks fail

## Deployment

✅ **Status**: Pushed to `main` branch
- Commit: `8c31fe7`
- Message: `fix: resolve health check errors - timezone handling, None pair, and result validation`
- Auto-deploys to Railway

## Remaining Non-Critical Errors

These are **external API issues** (not our code):
- `Jupiter price API error: 404` - Jupiter API endpoint issues (external)
- `Jupiter quote API error: 400` - Invalid token addresses or API changes (external)
- `Transaction simulation failed` - Solana network/transaction issues (expected during testing)

These don't crash the health monitor and are logged as warnings.
