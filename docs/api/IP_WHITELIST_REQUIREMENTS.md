# IP Whitelist Requirements for BitMart and Coinstore

**You're absolutely right!** Both exchanges require IP whitelisting.

---

## 🎯 **The Situation**

**Two servers need IP whitelisting:**
- **Railway:** `162.220.232.99` (static outbound IP - Railway Pro)
- **Hetzner:** `5.161.64.209` (static IP)

**Both exchanges need BOTH IPs whitelisted:**
- ✅ **Coinstore** - Required if API key has IP binding enabled
- ✅ **BitMart** - Required for all API keys

---

## 📋 **Coinstore IP Whitelisting**

### **How It Works:**
- Coinstore allows **up to 5 IPs per API key**
- If API key has **NO IPs bound** → Works from any IP
- If API key has **IPs bound** → **MUST** use one of those IPs

### **Current Status:**
- API Key: `42b5c7c40bf625e7fcffd16a654b6ed0`
- **Action Required:** Add BOTH IPs to IP binding list

### **How to Whitelist:**
1. Log into Coinstore dashboard
2. Go to API Key Management
3. Find API key: `42b5c7c40bf625e7fcffd16a654b6ed0`
4. Edit IP binding/IP whitelist
5. Add BOTH IPs:
   - `162.220.232.99` (Railway static IP)
   - `5.161.64.209` (Hetzner VPS)
6. Save changes

---

## 📋 **BitMart IP Whitelisting**

### **How It Works:**
- BitMart **always requires** IP whitelisting
- API keys won't work without whitelisted IPs
- Error `30010` = IP not whitelisted

### **Current Status:**
- BitMart bots showing IP forbidden errors
- **Action Required:** Add BOTH IPs to BitMart API key whitelist

### **How to Whitelist:**
1. Log into BitMart dashboard
2. Go to API Management
3. Find your BitMart API key
4. Edit IP whitelist
5. Add BOTH IPs:
   - `162.220.232.99` (Railway static IP)
   - `5.161.64.209` (Hetzner VPS)
6. Save changes

---

## ✅ **Summary**

| Exchange | IP Whitelist Required? | IPs to Whitelist | Status |
|----------|------------------------|-----------------|--------|
| **Coinstore** | ✅ Yes (if IP binding enabled) | `162.220.232.99` (Railway)<br>`5.161.64.209` (Hetzner) | ⏳ Needs whitelisting |
| **BitMart** | ✅ Yes (always required) | `162.220.232.99` (Railway)<br>`5.161.64.209` (Hetzner) | ⏳ Needs whitelisting |

---

## 🔧 **Why This Matters**

**Without IP whitelisting:**
- ❌ Coinstore: `1401 Unauthorized` error
- ❌ BitMart: `30010 IP forbidden` error
- ❌ Bots can't fetch balances
- ❌ Bots can't place orders

**With IP whitelisting:**
- ✅ Coinstore: Authentication succeeds
- ✅ BitMart: API calls work
- ✅ Bots fetch balances
- ✅ Bots can trade

---

## 🚀 **Action Items**

1. **Coinstore Dashboard:**
   - Add IP `162.220.232.99` (Railway) to IP binding list
   - Add IP `5.161.64.209` (Hetzner) to IP binding list
   - Save changes

2. **BitMart Dashboard:**
   - Add IP `162.220.232.99` (Railway) to API key whitelist
   - Add IP `5.161.64.209` (Hetzner) to API key whitelist
   - Save changes

3. **Test:**
   - Run `python3 test_coinstore_direct.py` on Hetzner
   - Check bot logs for BitMart errors
   - Verify balances show in dashboard

---

## 📝 **Note**

**You're correct:** Just creating an API key isn't enough. The exchange needs to know which IP addresses are allowed to use that key. This is a security feature to prevent unauthorized access.

**On Railway:**
- Railway Pro provides static outbound IP: `162.220.232.99`
- This IP needs to be whitelisted on **both** exchanges

**On Hetzner:**
- We have a static IP: `5.161.64.209`
- This IP also needs to be whitelisted on **both** exchanges

**Once both IPs are whitelisted:**
- ✅ Railway bots will work
- ✅ Hetzner bots will work
- ✅ Both servers can use the same API keys

---

**Bottom line:** Both exchanges need IP whitelisting. Add BOTH IPs (`162.220.232.99` and `5.161.64.209`) to Coinstore and BitMart API key whitelists.
