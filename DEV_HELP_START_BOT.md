# Dev Help Request - Start Bot Issue

**Date:** 2026-01-26  
**Issue:** `start_bot` fails with "Bot not found" after `deploy_script` succeeds

---

## 🔍 **Problem**

**Error from start_bot:**
```json
{"status":"success","response":{"success":false,"message":"Bot Test Bot UI not found"}}
```

**Hummingbot logs show:**
```
Bot Test Bot UI not found in active bots
```

**What's happening:**
1. ✅ `deploy_script` succeeds - Script is deployed to Hummingbot
2. ❌ `start_bot` fails - Bot instance not found in active bots

---

## 📋 **Current Flow**

```python
# 1. Deploy script
await self.hummingbot_client.deploy_script(
    script_content, 
    script_name,
    instance_name=name,
    credentials_profile=account
)
# ✅ This succeeds

# 2. Start bot
await self.hummingbot_client.start_bot(name, script_name, config)
# ❌ This fails: "Bot not found"
```

---

## ❓ **Questions**

1. **Does `deploy-v2-script` create the bot instance?**
   - Or do we need to create it separately?
   - Does it create it with a different name format?

2. **What's the correct flow?**
   - Should we call `start_bot` immediately after `deploy_script`?
   - Or is there a delay needed?
   - Or does the bot start automatically after deploy?

3. **What should we do?**
   - Skip `start_bot` and let bot start automatically?
   - Use a different endpoint to start the bot?
   - Wait a bit before calling `start_bot`?
   - Use a different bot name format?

---

## 🛠️ **Current Workaround**

I've made `start_bot` optional - if it fails, we log a warning but continue:

```python
try:
    await self.hummingbot_client.start_bot(name, script_name, config)
    logger.info(f"Started bot: {name}")
except Exception as start_error:
    logger.warning(f"Could not start bot immediately: {str(start_error)}. Bot may start automatically.")
    # Continue anyway - bot was deployed successfully
```

**But this might not be the right solution.**

---

## 📊 **Test Results**

**Direct curl test:**
```bash
curl -u admin:admin -H "ngrok-skip-browser-warning: true" \
  -X POST "https://...ngrok.../bot-orchestration/deploy-v2-script" \
  -H "Content-Type: application/json" \
  -d '{"script_content":"...","script_name":"test.py","instance_name":"test","credentials_profile":"client_sharp"}'
```
✅ **Succeeds**

```bash
curl -u admin:admin -H "ngrok-skip-browser-warning: true" \
  -X POST "https://...ngrok.../bot-orchestration/start-bot" \
  -H "Content-Type: application/json" \
  -d '{"bot_name":"test","script_file":"test.py","config":{}}'
```
❌ **Fails: "Bot test not found"**

---

## 🎯 **What We Need**

1. **Correct flow** - How should bot creation work?
2. **Instance naming** - What name format does Hummingbot use?
3. **Timing** - Do we need to wait after deploy?
4. **Alternative** - Is there a different way to start bots?

---

**Please advise on the correct Hummingbot API flow for creating and starting bots!** 🙏
