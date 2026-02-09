# Coinstore Two Keys - Solution Options

## Current Situation

You have **two Coinstore API keys**:

1. **"Pipe Labs"** 
   - Key: `42b5c7c40bf625e7fcffd16a654b6ed0`
   - IP: `3.222.129.4`
   - Status: Currently in database

2. **"second key"**
   - Key: `f2f0cb9e70c135e2cddfadc45c818cff`
   - IP: `54.205.35.75`
   - Status: Just created

**Problem:** Railway is using `54.205.35.75`, but database has "Pipe Labs" key whitelisted for `3.222.129.4`.

---

## ✅ Solution Options

### Option 1: Update Database to Use "second key" (Recommended)

**Best if:** You want to use the key that matches Railway's current IP.

**Steps:**
1. Get the API **secret** for "second key" (`f2f0cb9e70c135e2cddfadc45c818cff`)
2. Update database via API or directly:
   ```bash
   # Via API endpoint
   POST /api/cex/credentials
   {
     "exchange": "coinstore",
     "api_key": "f2f0cb9e70c135e2cddfadc45c818cff",
     "api_secret": "<SECRET_FOR_SECOND_KEY>"
   }
   ```
3. Delete "Pipe Labs" key from Coinstore (optional, to avoid confusion)

**Pros:**
- ✅ Matches Railway's current IP
- ✅ Cleaner (one key)
- ✅ Should work immediately

**Cons:**
- ❌ If Railway switches to `3.222.129.4`, will fail again

---

### Option 2: Update "Pipe Labs" Key to Include Both IPs (Best Long-term)

**Best if:** You want a single key that works regardless of which IP Railway uses.

**Steps:**
1. Go to Coinstore API Key Management
2. Edit "Pipe Labs" key (`42b5c7c40bf625e7fcffd16a654b6ed0`)
3. Update IP whitelist to include **BOTH**:
   ```
   3.222.129.4
   54.205.35.75
   ```
4. Save changes
5. Delete "second key" from Coinstore (optional)

**Pros:**
- ✅ Works with both Railway IPs
- ✅ No database changes needed
- ✅ Future-proof (works even if Railway switches IPs)

**Cons:**
- ⏳ Need to wait for Coinstore to propagate changes

---

### Option 3: Keep Both Keys (Not Recommended)

**Best if:** You want to test which one works better.

**Steps:**
- Keep both keys in Coinstore
- Update database to use "second key"
- Keep "Pipe Labs" key as backup

**Pros:**
- ✅ Backup option if one fails

**Cons:**
- ❌ More complex to manage
- ❌ Confusing which key is active
- ❌ Still need to update database

---

## 🎯 Recommendation

**Use Option 2: Update "Pipe Labs" key to include both IPs**

**Why:**
- ✅ No database changes needed
- ✅ Works with both Railway IPs
- ✅ Future-proof
- ✅ Single key to manage

**Steps:**
1. Edit "Pipe Labs" key in Coinstore
2. Add both IPs: `3.222.129.4` AND `54.205.35.75`
3. Save
4. Wait 1-2 minutes
5. Test dashboard
6. Delete "second key" (optional cleanup)

---

## 📝 Quick Decision Guide

**Choose Option 1 if:**
- You want quick fix
- Railway IP is stable
- You don't mind updating database

**Choose Option 2 if:**
- You want long-term solution
- Railway IPs alternate
- You want single key

**Choose Option 3 if:**
- You're testing
- You want backup options

---

## ✅ Expected Result

After implementing Option 2:
- ✅ Both Railway IPs whitelisted
- ✅ No more 1401 errors
- ✅ Balances will show
- ✅ Works regardless of which IP Railway uses
