# CTO: Confirm What Actually Runs When Starting Bot

**Question:** When client clicks "Start Bot", what code actually executes?

---

## Current Code Logic (bot_routes.py line 829-867)

When `POST /bots/{bot_id}/start` is called:

1. **Checks bot type:**
   ```python
   # Line 839-844: Determines if it's a CEX bot
   is_cex_bot = (
       bot.bot_type == 'volume' and 
       exchange and 
       exchange.lower() != 'jupiter' and
       chain != 'solana'
   )
   ```

2. **For Solana/EVM bots (line 847-853):**
   ```python
   if bot.bot_type in ['volume', 'spread'] and not is_cex_bot:
       bot.status = "running"
       await bot_runner.start_bot(bot_id, db)  # ← What does this do?
   ```

3. **For CEX bots (line 854-860):**
   ```python
   elif is_cex_bot:
       bot.status = "running"
       # CEX runner picks it up automatically
   ```

4. **For other bots (line 861-867):**
   ```python
   else:
       bot.status = "running"
       # TODO: Integrate with hummingbot_client
   ```

---

## Questions for CTO

### 1. Volume Bot with BitMart (CEX)
- **Is `cex_bot_runner.py` running?**
- **Does it use ccxt directly?**
- **Are API keys from `exchange_credentials` table?**

### 2. Spread Bot
- **Does it use Hummingbot?**
- **Is BitMart connector configured in Hummingbot?**
- **Are API keys in Hummingbot format?**

### 3. Bot Runner (`bot_runner.start_bot()`)
- **What does this actually do?**
- **Does it use Hummingbot or ccxt?**
- **Is it deployed and running?**

---

## What We Need to Know

**When client clicks "Start Bot" for a Volume Bot with BitMart:**

1. Does it call `bot_runner.start_bot()`? (Solana/EVM path)
2. Or does it set status and wait for `cex_bot_runner`? (CEX path)
3. What code actually executes the trades?

**If it's trying to use Hummingbot:**
- Hummingbot needs connector configured
- API keys in Hummingbot format
- Strategy file deployed

**If it's using ccxt (as designed for Volume Bot):**
- Should work with API keys from `exchange_credentials`
- Simpler, no Hummingbot needed

---

**Please confirm what code path actually runs when starting a Volume Bot with BitMart exchange.**
