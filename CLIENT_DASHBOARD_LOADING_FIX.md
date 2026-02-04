# Client Dashboard Loading Issue — Debug Guide

## 🔍 **Problem**

Client dashboard stuck on "Loading your dashboard..." screen.

---

## 🎯 **Likely Causes**

### **1. API Calls Failing**
ClientDashboard makes these calls on mount:
- `adminAPI.getClients()` - Get all clients
- `tradingBridge.getBots(accountId)` - Get client's bots
- `tradingBridge.getClientKeyStatus(clientId)` - Get key status

**Check:** Browser DevTools → Network tab → See which requests are failing

### **2. Database Migrations Not Run**
If migrations aren't run:
- Some columns might not exist
- Queries might fail
- API endpoints might error

**Fix:** Run migrations first!

### **3. Authentication Issue**
- Token expired or invalid
- Wallet address not matching
- User not found in database

**Check:** Browser Console → Look for auth errors

### **4. CORS Issue**
- Backend not allowing frontend origin
- Missing headers

**Check:** Network tab → CORS errors

---

## 🛠️ **Quick Fixes**

### **Fix 1: Check Browser Console**
1. Open client dashboard
2. Press F12 → Console tab
3. Look for errors (red text)
4. Share errors with me

### **Fix 2: Check Network Tab**
1. F12 → Network tab
2. Refresh page
3. Look for failed requests (red)
4. Check which endpoints are failing

### **Fix 3: Run Migrations**
If migrations not run, API calls might fail:
```bash
railway run python railway_migrate.py
```

---

## 📋 **Common Errors**

### **Error: "Failed to fetch client"**
- `adminAPI.getClients()` failing
- Check `/clients` endpoint

### **Error: "Failed to fetch bots"**
- `tradingBridge.getBots()` failing
- Check `/bots?account=...` endpoint

### **Error: "Failed to fetch key status"**
- `getClientKeyStatus()` failing
- Check `/clients/{id}/key-status` endpoint

---

## 🔧 **Debug Steps**

1. **Open Browser Console** (F12)
2. **Check for errors** - Share any red errors
3. **Check Network tab** - See which API calls fail
4. **Check if migrations run** - Run if not done
5. **Check authentication** - Verify token/wallet

---

**Share browser console errors and I'll help fix!**
