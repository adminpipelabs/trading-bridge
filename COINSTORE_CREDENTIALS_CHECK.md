# Coinstore Credentials Check

**Date:** February 10, 2026  
**Status:** Hetzner deployed, but Coinstore still returns 1401

---

## 🎯 **The Problem**

**1401 Unauthorized** from Coinstore even on Hetzner (no proxy).

**This means:**
- ✅ Infrastructure is fine (Hetzner works)
- ✅ Code is fine (spread bot works)
- ❌ Coinstore credentials/IP whitelist issue

---

## 🔍 **What to Check**

### **1. Verify IP Whitelist**

**On Coinstore Dashboard:**
1. Log into Coinstore
2. Go to API settings
3. Find API key: `42b5c7c40bf625e7fcffd16a654b6ed0`
4. Check IP whitelist
5. **Verify:** Is `5.161.64.209` listed?

**If not whitelisted:**
- Add `5.161.64.209` to whitelist
- Save
- Wait 1-2 minutes for propagation

---

### **2. Verify API Secret**

**Run on Hetzner:**
```bash
cd /opt/trading-bridge
source venv/bin/activate
python test_coinstore_credentials.py
```

**This will show:**
- API key from database
- API secret (first/last chars)
- Bot info

**Then:**
1. Log into Coinstore dashboard
2. Find API key `42b5c7c40bf625e7fcffd16a654b6ed0`
3. Compare secret in database vs Coinstore dashboard
4. **Do they match?**

**If secret doesn't match:**
- Secret in database is wrong
- Need to update database with correct secret

---

### **3. Check API Key Permissions**

**On Coinstore Dashboard:**
- API key `42b5c7c40bf625e7fcffd16a654b6ed0`
- Permissions should be:
  - ✅ Read enabled
  - ✅ Trade enabled
  - ✅ Spot trading enabled

---

### **4. Test with Official Example**

**Run on Hetzner:**
```bash
cd /opt/trading-bridge
source venv/bin/activate
python test_coinstore_official.py
```

**Or test endpoint:**
```bash
curl http://localhost:8080/test/coinstore
```

**Check response:**
- If 1401 → IP whitelist or secret issue
- If 200 with balance → Working!

---

## 🔧 **Possible Fixes**

### **Fix 1: Add IP to Whitelist**

**If IP not whitelisted:**
1. Coinstore dashboard → API settings
2. Find key `42b5c7c40bf625e7fcffd16a654b6ed0`
3. Add IP: `5.161.64.209`
4. Save
5. Wait 1-2 minutes
6. Test again

---

### **Fix 2: Update API Secret**

**If secret doesn't match:**

**Option A: Update database with correct secret**
```python
# Run on Hetzner
python update_coinstore_secret.py <correct_secret>
```

**Option B: Re-enter secret in database via UI/API**

---

### **Fix 3: Create New API Key**

**If credentials are completely wrong:**
1. Create new API key on Coinstore
2. Whitelist IP `5.161.64.209`
3. Update database with new key/secret
4. Test

---

## 📊 **Diagnostic Commands**

**On Hetzner server:**

```bash
# Check credentials in database
cd /opt/trading-bridge
source venv/bin/activate
python test_coinstore_credentials.py

# Test Coinstore API
curl http://localhost:8080/test/coinstore

# Check logs
journalctl -u trading-bridge -n 50 | grep -i coinstore
```

---

## 🎯 **Expected Result**

**After fixing IP whitelist/secret:**
- ✅ Status 200 from Coinstore
- ✅ Balance fetched successfully
- ✅ Orders placed
- ✅ No 1401 errors

---

**The app is ready. Just need to fix Coinstore credentials/IP whitelist.**
