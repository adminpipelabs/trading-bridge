# 🚨 Database Migration Required — Action Needed

**Priority:** HIGH  
**Time Required:** 2 minutes  
**Impact:** Fixes client role assignments to prevent security issues

---

## ✅ **What to Do**

Run these SQL commands in Railway PostgreSQL to fix client roles:

### **Step 1: Open Railway PostgreSQL Query Tab**
1. Go to Railway Dashboard
2. Select your PostgreSQL service
3. Click **"Query"** tab

### **Step 2: Run Migration SQL**
Copy and paste this SQL:

```sql
-- Set ALL non-admin users to 'client' role
UPDATE clients SET role = 'client' WHERE account_identifier != 'admin' OR account_identifier IS NULL;

-- Ensure only the actual admin has admin role
UPDATE clients SET role = 'admin' WHERE account_identifier = 'admin';

-- Set default for any NULL roles (safety)
UPDATE clients SET role = 'client' WHERE role IS NULL;
```

### **Step 3: Verify**
Run this query to confirm:

```sql
SELECT id, name, account_identifier, role FROM clients ORDER BY role, name;
```

**Expected Result:**
- ✅ All clients: `role = 'client'`
- ✅ Only admin: `role = 'admin'`
- ✅ NO NULL roles

---

## 🧪 **After Migration: Test Both Logins**

### **1. Test Client Login**
- Login with a client wallet (e.g., Lynk's Solana wallet)
- **Expected:** Should see **ClientDashboard**
- **Should NOT see:** Admin controls, other clients, admin routes

### **2. Test Admin Login**
- Login with admin wallet (`account_identifier = 'admin'`)
- **Expected:** Should see **AdminDashboard**
- **Should see:** All clients, admin controls, full access

### **3. Test Route Protection**
- As client, try navigating to `/#/admin`
- **Expected:** Should redirect to `/#/` (ClientDashboard)
- **Should NOT see:** Admin content

---

## 🔒 **Why This Matters**

This migration ensures:
- ✅ Clients cannot access admin dashboard
- ✅ Only admin account has admin privileges
- ✅ Database matches code security checks
- ✅ Multiple layers of protection work correctly

---

## 📋 **Status**

- ✅ Code fixes: Deployed
- ✅ Frontend routing: Fixed
- ✅ Backend role checks: Hardened
- ⚠️ **Database migration: PENDING** ← You are here

---

## ✅ **Once Complete**

After running the migration and testing:
1. ✅ All clients see ClientDashboard
2. ✅ Admin sees AdminDashboard
3. ✅ Route protection works
4. ✅ Security is fully enforced

**Then it's safe to onboard clients!**
