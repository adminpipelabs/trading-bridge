# Start Bot Issue - Bot Not Found

**Date:** 2026-01-26  
**Issue:** `start_bot` fails with "Bot not found" error

---

## 🔍 **Problem**

**Error from start_bot:**
```json
{"status":"success","response":{"success":false,"message":"Bot Test Bot UI not found"}}
```

**What's happening:**
1. ✅ `deploy_script` succeeds - Script is deployed
2. ❌ `start_bot` fails - Bot instance doesn't exist

---

## 🐛 **Root Cause**

`deploy-v2-script` endpoint deploys the script but doesn't create the bot instance. The `start-bot` endpoint expects the bot instance to already exist.

---

## 🛠️ **Possible Solutions**

### **Option 1: Check if deploy-v2-script creates instance**
- Maybe it does but with a different name format
- Check Hummingbot API docs for correct flow

### **Option 2: Create instance separately**
- There might be a separate endpoint to create bot instance
- Or instance is created automatically on first start

### **Option 3: Skip start_bot if not needed**
- Maybe bot starts automatically after deploy
- Or we need to call start differently

---

## 📋 **What to Check**

1. **Hummingbot API docs** - What's the correct flow?
2. **Check bot instances** - Do they exist after deploy?
3. **Test without start_bot** - See if bot starts automatically
4. **Check instance naming** - Maybe name format is wrong

---

## 🎯 **Next Steps**

1. Check Hummingbot API documentation
2. Check if instances are created after deploy
3. Test bot creation flow without start_bot
4. Fix based on findings

---

**Need to understand Hummingbot API flow!** 🔍
