# Railway Static IP Update

**Date:** February 5, 2026  
**Status:** Railway Pro static IP enabled

---

## 🎯 **Update**

**Railway now has a static outbound IP:**
- **IP:** `162.220.232.99`
- **Type:** Static outbound IP (Railway Pro feature)
- **Status:** ✅ Enabled and active

---

## 📋 **IP Whitelisting Required**

**Both servers need IP whitelisting:**

| Server | IP Address | Purpose |
|--------|------------|---------|
| **Railway** | `162.220.232.99` | Static outbound IP (Railway Pro) |
| **Hetzner** | `5.161.64.209` | VPS static IP |

---

## ✅ **Action Required**

### **Coinstore Dashboard:**

1. Log into Coinstore
2. Go to **API Management**
3. Find API key: `42b5c7c40bf625e7fcffd16a654b6ed0`
4. Click **Edit** → **IP Binding** / **IP Whitelist**
5. Add BOTH IPs:
   - `162.220.232.99` (Railway)
   - `5.161.64.209` (Hetzner)
6. Save changes

### **BitMart Dashboard:**

1. Log into BitMart
2. Go to **API Management**
3. Find your BitMart API key
4. Click **Edit** → **IP Whitelist**
5. Add BOTH IPs:
   - `162.220.232.99` (Railway)
   - `5.161.64.209` (Hetzner)
6. Save changes

---

## 🎯 **Why Both IPs?**

**Railway:**
- Running Trading Bridge app
- Uses static IP `162.220.232.99` for outbound requests
- Needs IP whitelisted to connect to exchanges

**Hetzner:**
- Also running Trading Bridge app (backup/redundancy)
- Uses static IP `5.161.64.209` for outbound requests
- Needs IP whitelisted to connect to exchanges

**Both can use the same API keys** once both IPs are whitelisted.

---

## ✅ **After Whitelisting**

**Expected results:**
- ✅ Railway bots connect successfully (no 1401 errors)
- ✅ Hetzner bots connect successfully (no 1401 errors)
- ✅ Both servers can fetch balances
- ✅ Both servers can place orders

---

## 📝 **Notes**

- **Railway Pro:** Provides static outbound IPs (no more dynamic IPs)
- **Coinstore:** Allows up to 5 IPs per API key (we're using 2)
- **BitMart:** Allows multiple IPs per API key (we're using 2)

---

**Once both IPs are whitelisted, both Railway and Hetzner will work!**
