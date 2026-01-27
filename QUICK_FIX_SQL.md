# Quick Fix - Add Missing Columns to Clients Table

**Copy and paste this SQL into Railway PostgreSQL Query Console:**

---

## 🚀 **Steps:**

1. **Railway Dashboard** → Click **PostgreSQL** service
2. Click **"Data"** tab or **"Query"** tab  
3. **Copy the SQL below** → Paste → Click **"Run"**

---

## 📋 **SQL to Run:**

```sql
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(100);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_type VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS tier VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'client';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
```

---

## ✅ **After Running:**

1. **Refresh admin page** - error will be gone
2. **Clients will load** without popup

---

**That's it! One SQL command fixes everything.**
