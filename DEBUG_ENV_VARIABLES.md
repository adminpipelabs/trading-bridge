# Debug Environment Variables

**Issue:** Variables set in Railway but not being read by application

---

## 🔍 **Step 1: Check Variable Names in Code**

**Verified variable names used in code:**

### **In `app/hummingbot_client.py`:**
```python
os.getenv("HUMMINGBOT_API_URL", "")           # Line 23
os.getenv("HUMMINGBOT_API_USERNAME", "hummingbot")  # Line 43
os.getenv("HUMMINGBOT_API_PASSWORD", "")      # Line 44
os.getenv("HUMMINGBOT_API_KEY", "")           # Line 45 (optional)
```

### **In `app/main.py`:**
```python
os.getenv("HUMMINGBOT_API_URL", "")           # Line 25
os.getenv("HUMMINGBOT_API_KEY", "")           # Line 35
os.getenv("HUMMINGBOT_API_PASSWORD", "")      # Line 36
```

**✅ Variable names are consistent:**
- `HUMMINGBOT_API_URL`
- `HUMMINGBOT_API_USERNAME`
- `HUMMINGBOT_API_PASSWORD`
- `HUMMINGBOT_API_KEY` (optional)

---

## 🧪 **Step 2: Test Debug Endpoint**

**After Railway redeploys (1-2 minutes), test:**

```bash
curl https://trading-bridge-production.up.railway.app/debug/env
```

**Expected output:**
```json
{
  "HUMMINGBOT_API_URL": "http://hummingbot-api:8000",
  "HUMMINGBOT_API_USERNAME": "admin",
  "has_password": true,
  "all_env_keys": ["HUMMINGBOT_API_URL", "HUMMINGBOT_API_USERNAME", "HUMMINGBOT_API_PASSWORD"]
}
```

**If variables not set:**
```json
{
  "HUMMINGBOT_API_URL": "NOT SET",
  "HUMMINGBOT_API_USERNAME": "NOT SET",
  "has_password": false,
  "all_env_keys": []
}
```

---

## 🔍 **Step 3: Verify in Railway**

### **Check Variables Tab:**

1. **Railway Dashboard** → **Trading Bridge service**
2. **Click "Variables" tab** (not Settings)
3. **Verify these exact names exist:**
   - `HUMMINGBOT_API_URL`
   - `HUMMINGBOT_API_USERNAME`
   - `HUMMINGBOT_API_PASSWORD`

### **Common Issues:**

- ❌ **Typo:** `HUMMINGBOT_API_URL` vs `HUMMINGBOT_API_URL` (missing S)
- ❌ **Wrong case:** `hummingbot_api_url` (should be all caps)
- ❌ **Extra spaces:** ` HUMMINGBOT_API_URL ` (leading/trailing spaces)
- ❌ **Not saved:** Variable added but "Save" button not clicked
- ❌ **Wrong service:** Variables set on different service

---

## 🚀 **Step 4: Force Redeploy**

**If variables are set but not being read:**

1. **Trading Bridge service** → **Settings**
2. **Click "Redeploy"** or make small change
3. **Wait 2-3 minutes**
4. **Test debug endpoint again**

---

## 📋 **Checklist**

- [ ] Variables exist in Railway Variables tab
- [ ] Variable names match exactly (all caps, no typos)
- [ ] Variables saved (not just typed)
- [ ] Service redeployed after setting variables
- [ ] Debug endpoint tested: `/debug/env`
- [ ] Debug endpoint shows variables are set
- [ ] Application logs checked after redeploy

---

## 🎯 **What to Share**

**After testing, share:**

1. **Debug endpoint output:**
   ```bash
   curl https://trading-bridge-production.up.railway.app/debug/env
   ```

2. **Railway Variables screenshot:**
   - Show Variables tab with all 3 variables visible

3. **Railway logs:**
   - Latest deployment logs
   - Any startup errors

---

## 🔧 **If Still Not Working**

**Possible causes:**

1. **Variables on wrong service** - Check they're on `trading-bridge` service
2. **Railway caching** - Try manual redeploy
3. **Project-level vs service-level** - Variables might need to be at project level
4. **Railway-specific issue** - May need Railway support

---

**Test the debug endpoint and share results!** 🔍
