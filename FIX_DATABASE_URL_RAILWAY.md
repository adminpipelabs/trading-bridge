# Fix DATABASE_URL in Railway - Step by Step

**Date:** 2026-01-26  
**Issue:** DATABASE_URL contains literal "host" instead of actual PostgreSQL hostname  
**Status:** Configuration issue, not code issue

---

## 🔍 **Problem**

The error shows:
```
could not translate host name "host" to address
```

**This means:** `DATABASE_URL` in Railway has a placeholder value instead of the real PostgreSQL connection string.

---

## ✅ **Solution: Fix DATABASE_URL in Railway**

### **Method 1: Copy URL from PostgreSQL Service (Recommended)**

**Step 1: Get Correct URL from PostgreSQL**
1. Go to Railway Dashboard: https://railway.app/dashboard
2. Click on **PostgreSQL** service (not trading-bridge)
3. Click **Connect** tab or **Variables** tab
4. Find `DATABASE_URL` - copy the **full value**

**Expected format:**
```
postgresql://postgres:ABC123xyz@monorail.proxy.rlwy.net:12345/railway
```

**NOT:**
```
postgresql://postgres:password@host:5432/database
```

---

**Step 2: Update Trading Bridge DATABASE_URL**
1. Railway Dashboard → Click on **trading-bridge** service
2. Click **Variables** tab
3. Find `DATABASE_URL`
4. **Click Edit** (or Delete and Add New)
5. **Paste** the correct URL from PostgreSQL service
6. **Save**

---

**Step 3: Redeploy**
- Railway will auto-redeploy
- Or click **Deployments** → **Redeploy**

**Wait:** 1-2 minutes for deployment

---

**Step 4: Test**
```bash
curl https://trading-bridge-production.up.railway.app/health
curl https://trading-bridge-production.up.railway.app/clients
curl https://trading-bridge-production.up.railway.app/bots
```

**Expected:** All endpoints should work now.

---

### **Method 2: Use Variable Reference (Alternative)**

**Instead of copying the URL, reference it directly:**

1. Railway Dashboard → **trading-bridge** → **Variables**
2. Find `DATABASE_URL` → **Delete** it
3. Click **"New Variable"** or **"Add Variable"**
4. Name: `DATABASE_URL`
5. Click **"Add Reference"** (link icon or dropdown)
6. Select **PostgreSQL** service
7. Select **DATABASE_URL** variable
8. Click **Add**

**Result:** Creates reference: `${{Postgres.DATABASE_URL}}`

Railway automatically resolves this to the correct URL.

---

## 📋 **What to Check**

**After updating DATABASE_URL, verify:**

1. **Format is correct:**
   - ✅ Starts with `postgresql://` or `postgres://`
   - ✅ Has real hostname (not "host")
   - ✅ Has port number
   - ✅ Has database name

2. **Example of correct format:**
   ```
   postgresql://postgres:password@monorail.proxy.rlwy.net:12345/railway
   ```

3. **Example of wrong format:**
   ```
   postgresql://postgres:password@host:5432/database
   ```

---

## 🎯 **Summary**

| Step | Action | Status |
|------|--------|--------|
| 1 | Get DATABASE_URL from PostgreSQL service | ⏳ |
| 2 | Update DATABASE_URL in trading-bridge | ⏳ |
| 3 | Redeploy | ⏳ |
| 4 | Test endpoints | ⏳ |

---

## ✅ **Code Status**

**The code is correct!** This is purely a Railway configuration issue.

**All fixes applied:**
- ✅ Sync routes
- ✅ psycopg2 driver
- ✅ Proper imports
- ✅ URL parsing logic

**Just need correct DATABASE_URL in Railway.**

---

**Follow these steps and endpoints should work!** 🚀
