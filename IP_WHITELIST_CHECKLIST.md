# IP Whitelist Checklist

**Status:** ⏳ Waiting for IP whitelisting

---

## ✅ **What's Been Done**

- ✅ Documentation updated with Railway static IP `162.220.232.99`
- ✅ Both IPs identified and documented
- ✅ Step-by-step instructions created
- ✅ Code verified (matches working open-source implementation)

---

## ⏳ **What Needs to Be Done**

### **Coinstore Dashboard**

- [ ] Log into Coinstore dashboard
- [ ] Go to API Management
- [ ] Find API key: `42b5c7c40bf625e7fcffd16a654b6ed0`
- [ ] Click Edit → IP Binding / IP Whitelist
- [ ] Add IP: `162.220.232.99` (Railway)
- [ ] Add IP: `5.161.64.209` (Hetzner)
- [ ] Save changes
- [ ] Wait 1-2 minutes for changes to propagate

### **BitMart Dashboard**

- [ ] Log into BitMart dashboard
- [ ] Go to API Management
- [ ] Find your BitMart API key
- [ ] Click Edit → IP Whitelist
- [ ] Add IP: `162.220.232.99` (Railway)
- [ ] Add IP: `5.161.64.209` (Hetzner)
- [ ] Save changes
- [ ] Wait 1-2 minutes for changes to propagate

---

## 🧪 **Testing After Whitelisting**

### **Test Railway (if running):**

```bash
# Check Railway logs
# Should see successful balance fetches, no 1401 errors
```

### **Test Hetzner:**

```bash
cd /opt/trading-bridge
source venv/bin/activate
python3 test_coinstore_direct.py
```

**Expected result:**
- ✅ Status Code: 200
- ✅ Response code: 0 (success)
- ✅ Balance data shown
- ❌ No 1401 errors

---

## ✅ **Success Indicators**

**Coinstore:**
- ✅ No `1401 Unauthorized` errors
- ✅ Balance fetches succeed
- ✅ Orders can be placed

**BitMart:**
- ✅ No `30010 IP forbidden` errors
- ✅ Balance fetches succeed
- ✅ Orders can be placed

---

## 📝 **Notes**

- **Coinstore:** Allows up to 5 IPs per API key (we're using 2)
- **BitMart:** Allows multiple IPs per API key (we're using 2)
- **Propagation:** Changes usually take effect within 1-2 minutes
- **Both servers:** Can use the same API keys once IPs are whitelisted

---

**Once both IPs are whitelisted on both exchanges, let me know and I'll verify everything is working!**
