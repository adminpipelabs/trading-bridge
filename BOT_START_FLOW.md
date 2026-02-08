# Bot Start Flow - Where Initiated & Approved

## Flow Diagram

```
1. CLIENT CLICKS "Start Bot" (ClientDashboard.jsx)
   ↓
2. handleStartStop() → tradingBridge.startBot(botId)
   ↓
3. apiCall() → POST /bots/{bot_id}/start
   ↓
4. BACKEND: Authorization Check (bot_routes.py line 808-824)
   ├─ Gets X-Wallet-Address header
   ├─ Calls get_current_client(wallet_address)
   ├─ Calls check_bot_access(bot, client)
   └─ If fails → checks Authorization token (admin fallback)
   ↓
5. BACKEND: Start Bot Logic (bot_routes.py line 826-867)
   ├─ Check bot type (Solana/EVM vs CEX)
   ├─ Set bot.status = "running"
   ├─ For Solana/EVM: Call bot_runner.start_bot()
   └─ For CEX: Just set status (CEX runner picks it up)
   ↓
6. RETURN: {"status": "started", "bot_id": "..."}
```

## Where Initiated

**Frontend:** `ai-trading-ui/src/pages/ClientDashboard.jsx`
- Line 167: `handleStartStop()` function
- Line 182: Calls `tradingBridge.startBot(botId)`

**API Call:** `ai-trading-ui/src/services/api.js`
- Line 389: `startBot()` function
- Uses `apiCall()` wrapper which adds headers

## Where Approved

**Backend:** `trading-bridge/app/bot_routes.py`
- Line 808-824: Authorization check
- Line 810: Gets `X-Wallet-Address` from header
- Line 814: Calls `get_current_client()` to find client
- Line 815: Calls `check_bot_access()` to verify ownership
- Line 816-819: If wallet auth fails, checks Authorization token

**Security Check:** `trading-bridge/app/security.py`
- Line 50-78: `get_current_client()` - finds client by wallet address
- Line 108-125: `check_bot_access()` - verifies client owns the bot

## What Actually Starts Bot

**After Authorization:**
- Line 847-853: Solana/EVM bots → `bot_runner.start_bot()`
- Line 854-860: CEX bots → Just set status, CEX runner picks up
- Line 861-867: Other bots → Just set status

## Current Issue

**Problem:** "Failed to fetch" - request never reaches server

**Possible causes:**
1. Browser blocking request (CORS, extension, security)
2. Wallet address not in database → `get_current_client()` fails → 401
3. Client doesn't own bot → `check_bot_access()` fails → 403

**Next step:** Check if wallet address is being sent correctly and if it exists in database.
