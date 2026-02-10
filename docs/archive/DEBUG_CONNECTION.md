# Debug Connection Error

**Status:** ❌ Internal Server Error  
**Next:** Check Railway logs to find the issue

---

## 🔍 **Check Trading Bridge Logs**

### **Step 1: Go to Railway Logs**

1. **Railway Dashboard** → Your Project
2. **Trading Bridge** service
3. **Deployments** tab
4. **Click latest deployment**
5. **View Logs** or **Logs** tab

### **Step 2: Look for Errors**

**Search for:**
- "HummingbotClient initialized"
- "Connection refused"
- "Name resolution failed"
- "Not authenticated"
- "Failed to connect"
- Any red error messages

**What error do you see?**

---

## 🎯 **Common Errors & Fixes**

### **Error 1: "Name resolution failed" or "Could not resolve"**

**Meaning:** Wrong service name

**Fix:** Service name is incorrect

**What to check:**
- What is the Hummingbot API service actually called?
- Check project overview - what's the exact name?

**Try:**
- `hummingbot` (without -api)
- Check if Railway auto-generated a name

---

### **Error 2: "Connection refused"**

**Meaning:** Can't reach Hummingbot API

**Possible causes:**
- Hummingbot API not running
- Wrong port
- Service not in same project

**Fix:**
- Check Hummingbot API is deployed
- Verify port is 8000
- Make sure both services in same project

---

### **Error 3: "Not authenticated"**

**Meaning:** Wrong credentials

**Fix:**
- Verify `HUMMINGBOT_API_USERNAME=admin`
- Verify `HUMMINGBOT_API_PASSWORD=admin`
- Check Hummingbot API variables match

---

### **Error 4: "Module not found" or Python error**

**Meaning:** Code issue

**Fix:**
- Check Trading Bridge deployment logs
- Verify code was deployed correctly

---

## 📋 **What to Share**

**Please share:**
1. **Error message from Trading Bridge logs**
2. **Any red/error lines**
3. **What it says after "HummingbotClient initialized"**

**OR take a screenshot of the error logs**

---

## 🔧 **Quick Fixes to Try**

### **Fix 1: Try Different Service Name**

**If error says "could not resolve":**

Try changing `HUMMINGBOT_API_URL` to:
- `http://hummingbot:8000` (without -api)
- Or check what Railway actually named it

### **Fix 2: Check Hummingbot API is Running**

**Go to Hummingbot API service:**
- Check **Logs** tab
- Should see "Uvicorn running on http://0.0.0.0:8000"
- If not running, check deployment errors

### **Fix 3: Verify Variables**

**In Trading Bridge Variables:**
- `HUMMINGBOT_API_URL=http://hummingbot-api:8000`
- `HUMMINGBOT_API_USERNAME=admin`
- `HUMMINGBOT_API_PASSWORD=admin`

**All three must be set!**

---

## ✅ **Next Steps**

1. **Check Trading Bridge logs** for error message
2. **Share the error** with me
3. **I'll help fix it** based on the error

**What error do you see in the logs?** 🔍
