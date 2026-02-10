# ⚠️ URGENT: IP Whitelist Update

**Status:** Need to add Railway IP as well

---

## 🎯 **Current Situation**

**You've requested whitelisting for:**
- ✅ `5.161.64.209` (Hetzner) - **Requested**

**But we also need:**
- ❌ `162.220.232.99` (Railway) - **Missing!**

---

## ⚠️ **Why Both IPs?**

**Railway:**
- Has static outbound IP: `162.220.232.99`
- Railway app is running Trading Bridge
- **Needs IP whitelisted** to connect to exchanges

**Hetzner:**
- Has static IP: `5.161.64.209`
- Also running Trading Bridge (backup/redundancy)
- **Needs IP whitelisted** to connect to exchanges

**Both servers need access** to use the same API keys.

---

## 🚨 **Action Required**

### **Update Request to SHARP Project:**

**Please ask them to whitelist BOTH IPs:**

**Coinstore:**
- `162.220.232.99` (Railway static IP)
- `5.161.64.209` (Hetzner VPS)

**BitMart:**
- `162.220.232.99` (Railway static IP)
- `5.161.64.209` (Hetzner VPS)

---

## 📋 **What Happens If Only One IP Is Whitelisted?**

**If only Hetzner IP (`5.161.64.209`) is whitelisted:**
- ✅ Hetzner bots will work
- ❌ Railway bots will fail with `1401 Unauthorized` (Coinstore) or `30010 IP forbidden` (BitMart)

**If only Railway IP (`162.220.232.99`) is whitelisted:**
- ✅ Railway bots will work
- ❌ Hetzner bots will fail with `1401 Unauthorized` (Coinstore) or `30010 IP forbidden` (BitMart)

**Both IPs must be whitelisted** for both servers to work.

---

## ✅ **Correct Request**

**Message to SHARP Project:**

> "Please whitelist these IPs on both Coinstore and BitMart API keys:
> 
> - `162.220.232.99` (Railway static outbound IP)
> - `5.161.64.209` (Hetzner VPS)
> 
> Both IPs are needed as we're running Trading Bridge on both servers."

---

## 🎯 **Summary**

| IP Address | Server | Status |
|------------|--------|--------|
| `162.220.232.99` | Railway | ⚠️ **Need to request** |
| `5.161.64.209` | Hetzner | ✅ Already requested |

**Action:** Update request to include Railway IP `162.220.232.99`
