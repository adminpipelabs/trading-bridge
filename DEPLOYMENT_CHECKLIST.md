# Deployment Checklist — Final Steps

**Date:** 2026-02-03  
**Status:** Code Deployed ✅ | Manual Setup Required ⚠️

---

## ✅ **Code Deployment Status**

### **Frontend (ai-trading-ui)**
- ✅ Client Dashboard redesign: `main` branch
- ✅ Help content & onboarding: `main` branch  
- ✅ Auto-deploys to Railway: **ACTIVE**

### **Backend (trading-bridge)**
- ✅ Authorization checks: `main` branch
- ✅ Health monitor fixes: `main` branch
- ✅ Auto-deploys to Railway: **ACTIVE**

---

## ⚠️ **Manual Setup Steps Required**

### **Step 1: Database Migrations** ⬜
**Location:** Railway Dashboard → PostgreSQL → Query tab

**Action:**
1. Open `migrations/COMPLETE_SETUP.sql`
2. Copy entire file contents
3. Railway Dashboard → PostgreSQL service → Query tab
4. Paste SQL → Click "Run"

**Verify:**
```sql
SELECT id, name, account_identifier, role FROM clients;
SELECT column_name FROM information_schema.columns WHERE table_name = 'bots' AND column_name = 'health_status';
SELECT table_name FROM information_schema.tables WHERE table_name = 'trading_keys';
```

**Expected:**
- ✅ All clients have correct roles
- ✅ `health_status` column exists
- ✅ `trading_keys` table exists

**Status:** ⬜ **TODO**

---

### **Step 2: Set ENCRYPTION_KEY** ⬜
**Location:** Railway Dashboard → trading-bridge → Variables

**Action:**
1. Railway Dashboard → trading-bridge service → Variables tab
2. Click "New Variable"
3. **Key:** `ENCRYPTION_KEY`
4. **Value:** `UA_gIhofKpjnIjxzqfjEKpGChl400tH_oo0Jq-WcXT8=`
5. Click "Add"
6. ⚠️ **Back up key** in password manager

**Verify:**
- Check Variables tab shows `ENCRYPTION_KEY` is set
- Service will auto-redeploy (~2-3 minutes)

**Status:** ⬜ **TODO**

---

### **Step 3: Wait for Redeploy** ⬜
**Location:** Railway Dashboard → trading-bridge → Deployments

**Action:**
- After adding ENCRYPTION_KEY, wait for latest deployment to show "Active"
- Usually takes 2-3 minutes

**Status:** ⬜ **TODO**

---

### **Step 4: Verification Tests** ⬜

#### **Automated Tests:**
```bash
cd /Users/mikaelo/trading-bridge
./VERIFICATION_COMMANDS.sh
```

#### **Manual Tests:**

**Test 1: Admin Login**
- [ ] Login with admin wallet
- [ ] Should see Admin Dashboard
- [ ] Should see all clients with correct roles
- [ ] Should see bot health statuses

**Test 2: Client Login (Lynk)**
- [ ] Login with Lynk wallet
- [ ] Should see Client Dashboard (NOT Admin)
- [ ] Should see welcome modal (first time)
- [ ] Should see Start/Stop/Edit buttons
- [ ] Should NOT see Delete button
- [ ] Should NOT see other clients' bots

**Test 3: Authorization**
- [ ] As client, try to start another client's bot
- [ ] Should get 403 Forbidden error

**Test 4: Health Monitor**
```bash
curl https://trading-bridge-production.up.railway.app/bots/health/summary
```
- [ ] Should return JSON with bot health statuses (not errors)

**Status:** ⬜ **TODO**

---

## 📋 **Progress Tracker**

| Step | Task | Status | Time |
|------|------|--------|------|
| 1 | Run database migrations | ⬜ | 5 min |
| 2 | Set ENCRYPTION_KEY | ⬜ | 2 min |
| 3 | Wait for redeploy | ⬜ | 2-3 min |
| 4 | Run verification tests | ⬜ | 10 min |

**Total:** ~17-20 minutes

---

## 🎯 **Success Criteria**

All items checked:
- [ ] Database migrations successful
- [ ] ENCRYPTION_KEY set
- [ ] Service redeployed
- [ ] Admin sees Admin Dashboard
- [ ] Client sees Client Dashboard (not admin)
- [ ] Clients can only manage own bots
- [ ] Health monitor working
- [ ] No errors in Railway logs

---

## 🚀 **Ready for Client Testing**

Once all steps complete:
- ✅ Client Dashboard fully functional
- ✅ Permissions enforced
- ✅ Help content available
- ✅ Health monitoring working
- ✅ Key management working

**MO can test with real client!**

---

## 📝 **Quick Reference**

- **Migration SQL:** `migrations/COMPLETE_SETUP.sql`
- **Encryption Key:** `UA_gIhofKpjnIjxzqfjEKpGChl400tH_oo0Jq-WcXT8=`
- **Verification Script:** `./VERIFICATION_COMMANDS.sh`
- **Detailed Instructions:** `SETUP_INSTRUCTIONS.md`

---

**Next:** Complete Steps 1-4 → Ready for client testing!
