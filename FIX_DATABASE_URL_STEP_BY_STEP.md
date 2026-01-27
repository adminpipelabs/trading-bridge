# Fix DATABASE_URL - Step by Step

**Dev's Instructions:** Use Railway Variable Reference (cleanest method)

---

## ✅ **Method 1: Railway Variable Reference (Recommended)**

This automatically links to PostgreSQL's DATABASE_URL - no manual password copying needed.

### Step 1: Delete Old DATABASE_URL
1. Railway Dashboard → **trading-bridge** service
2. Click **Variables** tab
3. Find `DATABASE_URL`
4. Click **Delete** (or edit and clear the value)

### Step 2: Add Reference to PostgreSQL
1. In **trading-bridge** → **Variables** tab
2. Click **"New Variable"** or **"Add Variable"**
3. Click **"Add Reference"** (small link icon or dropdown option)
4. Select **PostgreSQL** service from the list
5. Select **DATABASE_URL** from available variables
6. Click **Add** or **Save**

**Result:** Railway creates a reference like:
```
${{Postgres.DATABASE_URL}}
```

This automatically resolves to the correct URL with password.

---

## ✅ **Method 2: Manual Copy (If Reference Doesn't Work)**

### Step 1: Get Password from PostgreSQL
1. Railway Dashboard → **PostgreSQL** service
2. Click **Variables** tab
3. Find `POSTGRES_PASSWORD`
4. **Copy the entire password value**

### Step 2: Update trading-bridge DATABASE_URL
1. Railway Dashboard → **trading-bridge** service
2. Click **Variables** tab
3. Update `DATABASE_URL` to:
   ```
   postgresql://postgres:PASTE_PASSWORD_HERE@postgres.railway.internal:5432/railway
   ```
   Replace `PASTE_PASSWORD_HERE` with the password from Step 1.

**Example:**
```
postgresql://postgres:MQNSwgpfxGMmrlFXEKXPhcOKGEiINpEf@postgres.railway.internal:5432/railway
```

---

## ✅ **After Update**

Railway will **auto-redeploy** (wait 1-2 minutes).

### Test Connection:
```bash
# Health check
curl https://trading-bridge-production.up.railway.app/health

# Should return:
# {"status": "healthy", "database": "postgresql"}

# Test clients endpoint
curl https://trading-bridge-production.up.railway.app/clients

# Should return:
# {"clients": []}

# Test bots endpoint
curl https://trading-bridge-production.up.railway.app/bots

# Should return:
# {"bots": []}
```

---

## 🔍 **Verify DATABASE_URL Format**

After updating, check Railway logs. You should see:
```
INFO: Using DATABASE_URL format: postgresql+psycopg2://postgres:***@postgres.railway.internal:5432/railway
```

**NOT:**
```
ERROR: DATABASE_URL contains placeholder 'host'
```

---

## ✅ **Why Railway Variable Reference is Better**

- ✅ Automatically syncs if PostgreSQL password changes
- ✅ No manual password copying
- ✅ Railway handles the connection string
- ✅ Less error-prone

---

**Try Method 1 first (Railway Variable Reference). If it doesn't work, use Method 2 (manual copy).**
