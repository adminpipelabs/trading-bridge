# Verify Hummingbot API Service Name

**Status:** ✅ Variable set correctly (`http://hummingbot-api:8000`)  
**Issue:** Service name `hummingbot-api` not resolving

---

## 🔍 **What to Check**

### **Step 1: Find Actual Service Name**

**In Railway Dashboard:**

1. **Go to your Railway project**
2. **Look at the services list** (left sidebar or main view)
3. **Find the Hummingbot API service**
4. **What is it actually called?**

**Common names:**
- `hummingbot-api` ← You're using this
- `hummingbot` ← Might be this instead
- `hummingbot-api-production` ← Or this
- Something auto-generated

---

### **Step 2: Check Service Status**

**Click on Hummingbot API service:**

1. **Go to "Logs" tab**
2. **Look for:**
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   INFO:     Application startup complete
   ```

**If you see errors or it's not running:**
- Service might have failed to start
- Check deployment errors

---

### **Step 3: Verify Same Project**

**Check:**
- Are **Trading Bridge** and **Hummingbot API** in the **same Railway project**?
- Internal DNS only works within the same project
- If different projects, you'll need to use public URL instead

---

## 🔧 **Quick Fixes**

### **Fix 1: Try Different Service Name**

**If service is called `hummingbot` (without -api):**

1. **Trading Bridge** → **Variables**
2. **Change `HUMMINGBOT_API_URL` to:**
   ```
   http://hummingbot:8000
   ```
3. **Save and wait for redeploy**

### **Fix 2: Use Public URL**

**If services are in different projects:**

1. **Hummingbot API service** → **Settings**
2. **Generate Domain** (or check existing domain)
3. **Update Trading Bridge variable:**
   ```
   HUMMINGBOT_API_URL=https://hummingbot-api-production.up.railway.app
   ```
   (Use the actual public domain)

---

## 📋 **What We Need**

**Please check and tell me:**

1. **What is the Hummingbot API service actually called?**
   - Look at services list in Railway
   - Check service name/label

2. **Is Hummingbot API running?**
   - Check logs for "Uvicorn running"
   - Check deployment status

3. **Are both services in the same project?**
   - Trading Bridge and Hummingbot API should be together

---

## ✅ **Once We Know the Service Name**

**I'll help you:**
1. Update the variable to the correct name
2. Test the connection
3. Verify bot management works

---

**Please share what the Hummingbot API service is actually called in Railway!** 🔍
