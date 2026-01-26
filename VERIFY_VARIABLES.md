# Verify Environment Variables in Railway

**Issue:** Logs show `HUMMINGBOT_API_URL` not set, but you've already configured it.

---

## 🔍 **Step 1: Verify Variables Are Set**

### **In Railway Dashboard:**

1. **Go to Trading Bridge service**
2. **Click "Variables" tab**
3. **Check these exact variable names:**

**Required:**
- `HUMMINGBOT_API_URL` (exact spelling, all caps)
- `HUMMINGBOT_API_USERNAME`
- `HUMMINGBOT_API_PASSWORD`

**Common Issues:**
- ❌ Typo: `HUMMINGBOT_API_URL` vs `HUMMINGBOT_API_URL` (missing S)
- ❌ Wrong case: `hummingbot_api_url` (should be all caps)
- ❌ Extra spaces: ` HUMMINGBOT_API_URL ` (leading/trailing spaces)
- ❌ Not saved: Variable added but "Save" not clicked

---

## 🔧 **Step 2: Check Variable Values**

**For `HUMMINGBOT_API_URL`:**
- ✅ Should be: `http://hummingbot-api:8000` (or your service name)
- ❌ Should NOT be: `localhost:8000`
- ❌ Should NOT be: `http://localhost:8000`
- ❌ Should NOT be empty

**Format:**
- ✅ `http://[SERVICE_NAME]:8000`
- ✅ No trailing slash
- ✅ Use internal service name (not public URL)

---

## ✅ **Step 3: Verify Service Name**

**Check what Hummingbot API service is actually called:**

1. **Railway Dashboard** → **Your Project**
2. **Look at services list**
3. **What is Hummingbot API service called?**
   - Common: `hummingbot-api`, `hummingbot`
   - Check service settings if unsure

**Then verify `HUMMINGBOT_API_URL` matches:**
- If service is `hummingbot-api` → URL should be `http://hummingbot-api:8000`
- If service is `hummingbot` → URL should be `http://hummingbot:8000`

---

## 🚀 **Step 4: Force Redeploy**

**If variables are set correctly but still not working:**

1. **Trading Bridge service**
2. **Settings tab**
3. **Click "Redeploy"** or make a small change to trigger redeploy
4. **Wait 2-3 minutes**
5. **Check logs again**

---

## 🔍 **Step 5: Check Logs After Redeploy**

**Look for:**
```
✅ Good:
HummingbotClient initialized: http://hummingbot-api:8000 (auth: BASIC)

❌ Bad:
Configuration Error: HUMMINGBOT_API_URL is not set
```

---

## 📋 **Quick Checklist**

- [ ] Variables tab shows `HUMMINGBOT_API_URL` exists
- [ ] Variable name is exactly `HUMMINGBOT_API_URL` (all caps, no typos)
- [ ] Value is `http://[SERVICE_NAME]:8000` (not localhost)
- [ ] Service name matches actual Hummingbot API service name
- [ ] `HUMMINGBOT_API_USERNAME` is set
- [ ] `HUMMINGBOT_API_PASSWORD` is set
- [ ] Variables saved (not just typed)
- [ ] Service redeployed after setting variables
- [ ] Logs checked after redeploy

---

## 🎯 **Most Common Issues**

1. **Variable not saved** - Added but forgot to click "Save"
2. **Typo in variable name** - `HUMMINGBOT_API_URL` vs `HUMMINGBOT_API_URL`
3. **Wrong service name** - Using `localhost` instead of internal name
4. **Not redeployed** - Variables set but service not restarted
5. **Different project** - Services in different Railway projects

---

**Please verify these steps and let me know what you find!** 🔍
