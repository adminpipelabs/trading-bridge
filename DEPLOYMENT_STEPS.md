# PostgreSQL Persistence Deployment Steps

**Status:** ✅ Code ready - Follow steps below to deploy

---

## ✅ **What's Done**

1. ✅ Database models created (`app/database.py`)
2. ✅ Client routes with PostgreSQL (`app/clients_routes.py`)
3. ✅ Bot routes with PostgreSQL (`app/bot_routes.py`)
4. ✅ Main.py updated with database initialization
5. ✅ Requirements.txt already has SQLAlchemy and psycopg2-binary

---

## 📋 **Deployment Checklist**

### **Step 1: Add PostgreSQL Database in Railway** ⏳
- [ ] Go to Railway Dashboard → `trading-bridge` project
- [ ] Click **"New"** → **"Database"** → **"PostgreSQL"**
- [ ] Wait for provisioning (30 seconds)
- [ ] Copy `DATABASE_URL` from Variables tab

**Time:** 2 minutes

---

### **Step 2: Add DATABASE_URL to Trading Bridge** ⏳
- [ ] In Railway, click `trading-bridge` service
- [ ] Go to **"Variables"** tab
- [ ] Click **"New Variable"**
- [ ] Name: `DATABASE_URL`
- [ ] Value: Paste URL from Step 1
- [ ] Click **"Add"**

**Time:** 1 minute

---

### **Step 3: Verify Deployment** ⏳
After Railway redeploys (1-2 minutes):

```bash
# Check health
curl https://trading-bridge-production.up.railway.app/health
```

**Expected:**
```json
{"status": "healthy", "service": "Trading Bridge", "database": "postgresql"}
```

**Time:** 2 minutes

---

### **Step 4: Create Sharp Foundation Client** ⏳
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/clients/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sharp Foundation",
    "account_identifier": "client_sharp",
    "wallets": [
      {
        "chain": "evm",
        "address": "0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685"
      }
    ],
    "connectors": [
      {
        "name": "bitmart",
        "api_key": "d8550cca6914e2b24c6374fa1ef00fe0fce62c32",
        "api_secret": "0916719bcca31383406e9d9bdbadff0d104d94bbe58f50eb9e33337341de204f",
        "memo": "test1"
      }
    ]
  }'
```

**Time:** 1 minute

---

### **Step 5: Create Sharp Spread Bot** ⏳
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/bots/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sharp Spread",
    "account": "client_sharp",
    "connector": "bitmart",
    "pair": "SHARP/USDT",
    "strategy": "spread",
    "config": {
      "bid_spread": 0.003,
      "ask_spread": 0.003,
      "order_amount": 1600
    }
  }'
```

**Time:** 1 minute

---

### **Step 6: Verify Client Can See Bot** ⏳
```bash
# Look up client by wallet
curl "https://trading-bridge-production.up.railway.app/clients/by-wallet/0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685"

# Get bots for this account
curl "https://trading-bridge-production.up.railway.app/bots?account=client_sharp"
```

**Time:** 1 minute

---

### **Step 7: Test Persistence** ⏳
- [ ] Go to Railway Dashboard
- [ ] Click `trading-bridge` service
- [ ] Click **"Redeploy"**
- [ ] Wait for deploy to complete
- [ ] Run: `curl https://trading-bridge-production.up.railway.app/bots`
- [ ] Verify bots still exist

**Time:** 2 minutes

---

## 🎯 **Expected Results**

**After deployment:**
- ✅ Clients persist across restarts
- ✅ Bots persist across restarts
- ✅ Wallet → Account mapping works
- ✅ Client can see their bots
- ✅ Admin can manage bots

**Total deployment time:** ~10 minutes

---

## 📝 **Notes**

- **Auto-sync:** New clients created in Pipe Labs dashboard will auto-sync to trading-bridge
- **Account identifier:** Auto-generated from client name (e.g., "Sharp Foundation" → `client_sharp_foundation`)
- **Manual override:** Can specify `account_identifier` when creating client

---

**Ready to deploy!** 🚀
