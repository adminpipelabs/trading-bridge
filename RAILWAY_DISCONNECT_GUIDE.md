# Railway Disconnect Guide

**Question:** Should we disconnect Railway?

**Answer:** **Partially** - Keep Postgres, stop the app service

---

## 🎯 **What Hetzner Needs from Railway**

### ✅ **Keep Running:**
- **Postgres Database** - Hetzner still uses Railway's Postgres
  - `DATABASE_URL` points to Railway Postgres
  - Contains all bot data, credentials, configs
  - **DO NOT disconnect this**

### ❌ **Can Stop:**
- **Trading Bridge App Service** - No longer needed
  - Hetzner is running the app now
  - Railway app was using broken proxy
  - **Safe to stop/deploy**

---

## 📋 **IP Whitelisting - Only One IP**

### **Whitelist ONLY:**
- ✅ **`5.161.64.209`** - Hetzner server static IP

### **Do NOT whitelist:**
- ❌ `3.222.129.4` - Old QuotaGuard proxy IP (not used)
- ❌ `54.205.35.75` - Old QuotaGuard proxy IP (not used)
- ❌ Railway dynamic IPs - Not needed

**Why?**
- Hetzner connects **directly** (no proxy)
- Only Hetzner's static IP `5.161.64.209` makes requests
- Proxy IPs are from Railway days (no longer used)

---

## 🔧 **Current Setup**

```
Hetzner Server (5.161.64.209)
├── Trading Bridge App ✅ Running
└── Connects to → Railway Postgres ✅ Still needed

Railway
├── Trading Bridge App ❌ Can stop
└── Postgres Database ✅ Keep running
```

---

## 🚀 **Action Plan**

### **Step 1: Whitelist IPs (Do This First)**

**Coinstore:**
- Add ONLY `5.161.64.209` to IP binding list

**BitMart:**
- Add ONLY `5.161.64.209` to IP whitelist

### **Step 2: Verify Hetzner Works**

```bash
# On Hetzner
python3 test_coinstore_direct.py
```

**Should see:** Balance data (not 1401 error)

### **Step 3: Stop Railway App (Optional)**

**Railway Dashboard:**
1. Go to Trading Bridge service
2. Click "Settings" → "Delete" or "Stop"
3. **Keep Postgres running!**

**Or just leave it:** Railway app won't interfere, just costs money

### **Step 4: Verify Database Connection**

**On Hetzner:**
```bash
psql $DATABASE_URL
```

**Should connect:** Railway Postgres allows Hetzner IP

**If connection fails:**
- Railway Postgres might block Hetzner IP
- Need to whitelist `5.161.64.209` in Railway Postgres settings
- Or migrate database to Hetzner (more complex)

---

## ⚠️ **Important Notes**

### **Database Migration (Future)**

**Eventually you might want to:**
- Move Postgres to Hetzner (local database)
- Or use managed Postgres (AWS RDS, DigitalOcean, etc.)
- **But not urgent** - Railway Postgres works fine

### **Railway Postgres IP Whitelist**

**If Hetzner can't connect:**
- Railway Postgres might have IP restrictions
- Check Railway Postgres settings
- Add `5.161.64.209` to allowed IPs
- Or disable IP restrictions (if possible)

---

## ✅ **Summary**

| Component | Action | Reason |
|-----------|--------|--------|
| **IP Whitelist** | Add ONLY `5.161.64.209` | Hetzner's static IP |
| **Railway App** | Can stop | Hetzner runs app now |
| **Railway Postgres** | Keep running | Hetzner still uses it |
| **Proxy IPs** | Don't whitelist | Not used anymore |

---

## 🎯 **Bottom Line**

1. ✅ **Whitelist ONLY `5.161.64.209`** on both exchanges
2. ✅ **Keep Railway Postgres running** (Hetzner needs it)
3. ⚠️ **Railway app can be stopped** (saves money, not required)
4. ❌ **Don't whitelist proxy IPs** (not used on Hetzner)

**Railway Postgres is still needed until you migrate the database.**
