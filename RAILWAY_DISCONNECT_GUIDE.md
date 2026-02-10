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

### ⚠️ **Can Keep Running (Optional):**
- **Trading Bridge App Service** - Can run on both servers
  - Railway now has static IP `162.220.232.99` (no proxy needed)
  - Hetzner also running (redundancy/backup)
  - **Both can run simultaneously** (redundancy)
  - **Or stop Railway** to save costs (Hetzner handles it)

---

## 📋 **IP Whitelisting - Two IPs Required**

### **Whitelist BOTH:**
- ✅ **`162.220.232.99`** - Railway static outbound IP (Railway Pro)
- ✅ **`5.161.64.209`** - Hetzner server static IP

### **Do NOT whitelist:**
- ❌ `3.222.129.4` - Old QuotaGuard proxy IP (not used)
- ❌ `54.205.35.75` - Old QuotaGuard proxy IP (not used)

**Why both?**
- Railway Pro now provides static outbound IP `162.220.232.99`
- Hetzner uses static IP `5.161.64.209`
- Both servers can run Trading Bridge (redundancy/backup)
- Both need IP whitelisted to use the same API keys

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
- Add `162.220.232.99` (Railway) to IP binding list
- Add `5.161.64.209` (Hetzner) to IP binding list

**BitMart:**
- Add `162.220.232.99` (Railway) to IP whitelist
- Add `5.161.64.209` (Hetzner) to IP whitelist

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
| **IP Whitelist** | Add BOTH IPs | Railway: `162.220.232.99`<br>Hetzner: `5.161.64.209` |
| **Railway App** | Can keep running | Static IP enabled, no proxy needed |
| **Railway Postgres** | Keep running | Both servers use it |
| **Proxy IPs** | Don't whitelist | Not used anymore |

---

## 🎯 **Bottom Line**

1. ✅ **Whitelist BOTH IPs** on both exchanges:
   - `162.220.232.99` (Railway static IP)
   - `5.161.64.209` (Hetzner static IP)
2. ✅ **Keep Railway Postgres running** (both servers use it)
3. ⚠️ **Railway app can keep running** (now has static IP, works without proxy)
   - Or stop it to save costs (Hetzner handles it)
4. ❌ **Don't whitelist proxy IPs** (not used anymore)

**Railway Pro provides static IP, so Railway app can work without proxy. Both servers can run simultaneously for redundancy, or you can stop Railway to save costs.**
