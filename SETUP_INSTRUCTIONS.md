# Setup Instructions — Final Steps Before Client Testing

**Time Required:** ~17 minutes  
**Status:** Code is deployed, setup steps remaining

---

## Step 1: Run Database Migrations (5 minutes)

### **Action:**
1. Open Railway Dashboard
2. Go to your **PostgreSQL** service
3. Click **"Query"** tab
4. Copy **entire contents** of `migrations/COMPLETE_SETUP.sql`
5. Paste into Query tab
6. Click **"Run"** or **"Execute"**

### **Verify:**
After running, you should see:
- ✅ All clients have correct roles (admin = 'admin', others = 'client')
- ✅ `health_status` column exists on bots table
- ✅ `trading_keys` table exists
- ✅ `bot_health_logs` table exists

**If errors:** Check Railway logs. Most errors are harmless (IF NOT EXISTS clauses).

---

## Step 2: Set ENCRYPTION_KEY (2 minutes)

### **Generate Key:**
Run this command locally:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Or use the generated key below (if provided).

### **Action:**
1. Open Railway Dashboard
2. Go to **trading-bridge** service
3. Click **"Variables"** tab
4. Click **"New Variable"**
5. **Key:** `ENCRYPTION_KEY`
6. **Value:** (paste generated key)
7. Click **"Add"**

### **Important:**
- ⚠️ **Back up this key** in a password manager
- ⚠️ If lost, all encrypted keys become unrecoverable
- Service will auto-redeploy after adding variable (~2-3 minutes)

---

## Step 3: Wait for Redeploy (2-3 minutes)

After adding ENCRYPTION_KEY:
- Railway will automatically redeploy the service
- Check Railway Dashboard → trading-bridge → Deployments
- Wait for latest deployment to show "Active"

---

## Step 4: Verify Everything (10 minutes)

### **Automated Tests:**
Run the verification script:
```bash
chmod +x VERIFICATION_COMMANDS.sh
./VERIFICATION_COMMANDS.sh
```

### **Manual Tests:**

#### **Test 1: Admin Login**
1. Login with admin wallet
2. ✅ Should see **Admin Dashboard**
3. ✅ Go to Clients → Should see all clients with correct roles
4. ✅ Go to Bots → Should see health statuses (not all "Error")

#### **Test 2: Client Login (Lynk)**
1. Login with Lynk wallet (`2REe...yKMq`)
2. ✅ Should see **Client Dashboard** (NOT Admin Dashboard)
3. ✅ Should see welcome modal (first time only)
4. ✅ Should see overview cards (Bot Status, Wallet Balance, Volume)
5. ✅ Should see "Connect Wallet Key" banner (if key not connected)
6. ✅ Should see Start/Stop/Edit buttons
7. ✅ Should **NOT** see Delete button
8. ✅ Should **NOT** see other clients' bots
9. ✅ Should **NOT** see admin controls

#### **Test 3: Authorization**
1. As client, try to start another client's bot (if you know another bot ID)
2. ✅ Should get 403 Forbidden error
3. ✅ Should only be able to manage own bots

#### **Test 4: Health Monitor**
```bash
curl https://trading-bridge-production.up.railway.app/bots/health/summary
```
**Expected:** JSON response with bot health statuses (not errors)

#### **Test 5: Key Status**
```bash
curl https://trading-bridge-production.up.railway.app/clients/{client_id}/key-status
```
**Expected:** JSON response with key status

---

## ✅ **Success Criteria**

All tests pass:
- ✅ Database migrations successful
- ✅ ENCRYPTION_KEY set
- ✅ Admin sees Admin Dashboard
- ✅ Client sees Client Dashboard (not admin)
- ✅ Clients can only manage own bots
- ✅ Health monitor working
- ✅ No errors in Railway logs

---

## 🎯 **Ready for Client Testing**

Once all steps complete and verification passes:
- ✅ Client Dashboard fully functional
- ✅ Permissions enforced
- ✅ Help content available
- ✅ Health monitoring working
- ✅ Key management working

**MO can now test with a real client!**

---

## 🆘 **Troubleshooting**

### **Migration Errors:**
- Most errors are harmless (IF NOT EXISTS clauses)
- Check Railway logs for specific errors
- Re-run individual migration sections if needed

### **ENCRYPTION_KEY Issues:**
- Service won't start if key is missing
- Check Railway Variables tab
- Verify key is correct format (Fernet key)

### **Authorization Errors:**
- Check Railway logs for 403 errors
- Verify client roles in database
- Verify X-Wallet-Address header is sent

### **Health Monitor Errors:**
- Check Railway logs
- Verify health columns exist
- Check bot_health_logs table exists

---

## 📝 **Files Reference**

- `migrations/COMPLETE_SETUP.sql` - Complete migration SQL
- `VERIFICATION_COMMANDS.sh` - Automated test script
- `FINAL_CHECKLIST_STATUS.md` - Full status document

---

**Next:** Run Step 1 (migrations) → Step 2 (ENCRYPTION_KEY) → Verify → Ready!
