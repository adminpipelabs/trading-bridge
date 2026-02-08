# Confirmed: Bot Start Logic

## Volume Bot with BitMart (CEX)

**When client clicks "Start Bot":**

1. **Frontend:** `POST /bots/{bot_id}/start` → **Currently failing with "Failed to fetch"**

2. **Backend (if request reaches it):**
   - Line 839-844: Detects it's a CEX bot (`is_cex_bot = True`)
   - Line 854-860: Sets `bot.status = "running"` and commits
   - **Does NOT call Hummingbot** - Hummingbot is TODO
   - **Does NOT call bot_runner.start_bot()** - Only for Solana/EVM
   - Just sets status, CEX runner picks it up

3. **CEX Bot Runner** (runs in background):
   - Started in `main.py` line 148-156
   - Uses `cex_volume_bot.py` which uses **ccxt** (not Hummingbot)
   - Picks up bots with `status = 'running'`
   - Executes trades using ccxt library

## Current Issue

**"Failed to fetch" happens BEFORE step 2** - the request never reaches the backend.

**This is a frontend fetch() issue, not a bot execution issue.**

The bot execution logic is correct:
- ✅ Uses ccxt (not Hummingbot)
- ✅ CEX runner is configured
- ✅ Code path is correct

**The problem is:** Browser fetch() is failing before the request reaches the server.

---

## What We've Pushed

1. ✅ Debug logging in `startBot()` function
2. ✅ Debug logging in `handleStartStop()` function
3. ✅ Fixed authorization logic
4. ✅ Simplified fetch call

**Next:** Check browser console for DEBUG logs to see where exactly it fails.
