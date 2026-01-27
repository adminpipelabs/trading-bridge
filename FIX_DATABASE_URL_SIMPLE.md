# Fix DATABASE_URL - Simple Steps

**From Dev:** This is NOT a code problem. DATABASE_URL has placeholder "host" instead of real hostname.

---

## ✅ **2-Minute Fix**

### **Step 1: Get Real URL from PostgreSQL**

1. Railway Dashboard → https://railway.app/dashboard
2. Click **PostgreSQL** service (database icon)
3. Click **"Connect"** tab
4. Copy the **DATABASE_URL** value

**Should look like:**
```
postgresql://postgres:aBcDeFgHiJkLmNoP@monorail.proxy.rlwy.net:12345/railway
```

---

### **Step 2: Update Trading Bridge**

1. Railway Dashboard → Click **trading-bridge** service
2. Click **"Variables"** tab
3. Find `DATABASE_URL` → **Delete** it
4. Click **"New Variable"**
5. Name: `DATABASE_URL`
6. Value: **Paste the URL from Step 1**
7. **Save**

---

### **Step 3: Wait for Redeploy**

Railway auto-redeploys (1-2 minutes)

---

### **Step 4: Test**

```bash
curl https://trading-bridge-production.up.railway.app/health
```

**Expected:**
```json
{"status": "healthy", "database": "postgresql"}
```

---

## ❌ **What's Wrong**

**Current (wrong):**
```
postgresql://postgres:password@host:5432/database
```

**Needed (correct):**
```
postgresql://postgres:password@monorail.proxy.rlwy.net:12345/railway
```

**The word `host` is a placeholder - needs real Railway hostname.**

---

**No code changes needed. Just fix DATABASE_URL in Railway.** ✅
