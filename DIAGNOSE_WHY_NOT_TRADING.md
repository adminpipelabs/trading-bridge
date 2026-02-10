# Why Bot Is Not Trading - Diagnostic Steps

**Check Hetzner logs in this order:**

## **1. Is CEX Bot Runner Starting?**

```bash
ssh root@5.161.64.209
journalctl -u trading-bridge -f | grep -i "CEX Bot Runner\|Starting CEX"
```

**Look for:**
- ✅ `"Starting CEX bot runner..."`
- ✅ `"✅ CEX bot runner started"`
- ✅ `"🔄 CEX Bot Runner cycle starting"`

**If missing:** Bot runner not starting → Check main.py startup

---

## **2. Is Bot Being Found?**

```bash
journalctl -u trading-bridge -f | grep -i "Found.*CEX bots\|Processing.*bot"
```

**Look for:**
- ✅ `"✅ Found X CEX bots from main query"`
- ✅ `"📋 Processing X bot(s)..."`
- ✅ `"🔍 Processing bot: {id} (SHARP Volume Bot...)"`

**If `Found 0 bots`:** Bot not in database OR query filtering it out

---

## **3. Is Bot Being Initialized?**

```bash
journalctl -u trading-bridge -f | grep -i "Initializing\|Initialized CEX bot\|Failed to initialize"
```

**Look for:**
- ✅ `"🔄 Bot {id} not in active_bots - Initializing..."`
- ✅ `"✅ SUCCESS: Initialized CEX bot"`
- ❌ `"❌ FAILED: Could not initialize CEX bot"`

**If failed:** Check exchange connection, API keys, credentials

---

## **4. Is Timing Logic Working?**

```bash
journalctl -u trading-bridge -f | grep -i "Checking trade timing\|WILL TRADE\|WAITING\|Elapsed"
```

**Look for:**
- ✅ `"🔍 Bot {id} - Checking trade timing"`
- ✅ `"✅ Bot {id} - First trade (no last_trade_time) - WILL TRADE NOW"`
- ✅ `"🔍 Bot {id} - Elapsed: Xs / Ys - WILL TRADE"`

**If always "WAITING":** Timing logic issue - check interval calculation

---

## **5. Is Trade Execution Being Called?**

```bash
journalctl -u trading-bridge -f | grep -i "EXECUTING TRADE NOW\|Starting trade cycle\|CALLING create_market"
```

**Look for:**
- ✅ `"🔄 EXECUTING TRADE NOW - Bot {id}"`
- ✅ `"🔄 Starting trade cycle"`
- ✅ `"🚀 CALLING create_market_buy_order() NOW"`

**If missing:** `should_trade = False` or `run_single_cycle()` not being called

---

## **6. Are Orders Failing?**

```bash
journalctl -u trading-bridge -f | grep -i "ORDER FAILED\|Trade execution failed\|Insufficient funds"
```

**Look for:**
- ❌ `"❌ ORDER FAILED: Trade execution failed"`
- ❌ `"Insufficient funds"`
- ❌ `"Invalid order"`

**If errors:** Check exchange API, balances, order parameters

---

## **Quick Check Command (All at Once)**

```bash
ssh root@5.161.64.209
journalctl -u trading-bridge --since "5 minutes ago" | grep -E "CEX Bot Runner|Found.*CEX bots|Initialized CEX bot|EXECUTING TRADE NOW|ORDER FAILED|WILL TRADE|WAITING" | tail -50
```

---

## **Most Likely Issues:**

1. **Bot runner not starting** → Check `main.py` startup logs
2. **Bot not found** → Check database query (LEFT JOIN fix should help)
3. **Bot not initializing** → Check credentials, exchange connection
4. **Timing logic** → Bot waiting for interval (check `last_trade_time`)
5. **Order execution failing** → Check exchange API errors

**Check logs now to see which step is failing.**
