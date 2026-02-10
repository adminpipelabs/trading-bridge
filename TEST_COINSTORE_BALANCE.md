# Test Coinstore Balance - Step 1

**Goal:** Verify Coinstore balance fetching works after IP whitelisting

---

## 🧪 **Option 1: Test Script (Recommended)**

**On Hetzner:**
```bash
cd /opt/trading-bridge
source venv/bin/activate
python3 test_coinstore_balance.py
```

**Expected Output:**
```
✅ SUCCESS! Balance fetch working!
Found X account entries:

Balances:
  SHARP     Available:     12345.67890000  Frozen:      0.00000000  Total:     12345.67890000
  USDT      Available:      1500.12345678  Frozen:      0.00000000  Total:      1500.12345678
```

**If you see 1401 error:**
- Wait 1-2 minutes (IP whitelist propagation)
- Try again

---

## 🧪 **Option 2: Test via API Endpoint**

**If backend is running on Hetzner:**

```bash
# Get account identifier (e.g., client_sharp)
ACCOUNT="client_sharp"

# Test balance endpoint
curl http://localhost:8080/api/exchange/balance/${ACCOUNT}
```

**Expected Response:**
```json
{
  "account": "client_sharp",
  "balances": {
    "coinstore": {
      "SHARP": {
        "total": 12345.6789,
        "free": 12345.6789,
        "used": 0.0
      },
      "USDT": {
        "total": 1500.1234,
        "free": 1500.1234,
        "used": 0.0
      }
    }
  },
  "total_usdt": 1500.1234
}
```

---

## 🧪 **Option 3: Test Bot Balance Endpoint**

**If you have a Coinstore bot:**

```bash
# Get bot ID
BOT_ID="your_coinstore_bot_id"

# Test bot balance
curl http://localhost:8080/api/bots/${BOT_ID}/balance-and-volume
```

**Expected Response:**
```json
{
  "bot_id": "...",
  "available": {
    "SHARP": 12345.6789,
    "USDT": 1500.1234
  },
  "locked": {
    "SHARP": 0.0,
    "USDT": 0.0
  },
  ...
}
```

---

## ✅ **Success Criteria**

**Balance fetching is working when:**
- ✅ No `1401 Unauthorized` errors
- ✅ Response code is `0` (success)
- ✅ Balance data is returned (SHARP, USDT, etc.)
- ✅ Amounts are > 0 (if you have funds)

---

## 🐛 **Troubleshooting**

### **Still getting 1401:**
1. Wait 1-2 minutes after IP whitelisting
2. Verify IPs are actually whitelisted in Coinstore dashboard
3. Check API key permissions (Spot Trading enabled)

### **No balance data:**
- Check if account has funds
- Verify API key is correct
- Check logs for other errors

### **Connection errors:**
- Check Hetzner server is running
- Verify DATABASE_URL and ENCRYPTION_KEY are set
- Check network connectivity

---

## 📋 **Next Steps After Balance Works**

1. ✅ Balance fetching works
2. ⏳ Test bot creation
3. ⏳ Test bot start/stop
4. ⏳ Test trading

---

**Run the test script and let me know the results!**
