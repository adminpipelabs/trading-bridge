# Coinstore Balance Test - Verification

**Status:** ✅ Test script ready  
**Next:** Run test on Hetzner server

---

## ✅ **Code Verification**

**Implementation Check:**
- ✅ `CoinstoreConnector.get_balances()` uses correct endpoint: `/spot/accountList`
- ✅ Signature generation matches official Coinstore docs (two-step HMAC-SHA256)
- ✅ Headers correct: `X-CS-APIKEY`, `X-CS-SIGN`, `X-CS-EXPIRES`
- ✅ Payload correct: `'{}'` for empty POST request
- ✅ No proxy on Hetzner (direct connection)
- ✅ Error handling for 1401 includes detailed diagnostics

**Balance Parsing:**
- ✅ Handles list format response
- ✅ Groups AVAILABLE (type 1) and FROZEN (type 4) correctly
- ✅ Returns `{free: {}, used: {}, total: {}}` format

---

## 🧪 **Test Script: `test_coinstore_balance.py`**

**What it does:**
1. Loads Coinstore credentials from database
2. Creates `CoinstoreConnector` (no proxy)
3. Calls `get_balances()` → `/api/spot/accountList`
4. Parses response and displays balances

**Expected Output (Success):**
```
============================================================
Coinstore Balance Test
============================================================

✅ Loaded credentials for account: client_sharp
   API Key: 42b5c7c40b...654b6ed0
   Secret: abc12...xyz

📡 Fetching balance from Coinstore...
   Endpoint: POST /api/spot/accountList

============================================================
Response Received
============================================================

Response Code: 0
Message: success
Data Type: <class 'list'>

✅ SUCCESS! Balance fetch working!

Found 4 account entries:

Balances:
------------------------------------------------------------
  SHARP     Available:     12345.67890000  Frozen:      0.00000000  Total:     12345.67890000
  USDT      Available:      1500.12345678  Frozen:      0.00000000  Total:      1500.12345678

✅ Balance fetching is working correctly!
```

**Expected Output (1401 Error):**
```
❌ Error: Code 1401, Message: Unauthorized

⚠️  1401 Unauthorized - IP whitelist may not be active yet
   Wait 1-2 minutes after whitelisting and try again
```

---

## 🚀 **How to Run Test**

**On Hetzner Server:**
```bash
cd /opt/trading-bridge
source venv/bin/activate
python3 test_coinstore_balance.py
```

**Or via API endpoint (if backend running):**
```bash
curl http://localhost:8080/test/coinstore
```

---

## ✅ **Success Criteria**

**Test passes when:**
- ✅ Response code is `0` (not 1401)
- ✅ Data is a list with account entries
- ✅ Balances are displayed (SHARP, USDT, etc.)
- ✅ No exceptions thrown

**If test passes:**
- ✅ IP whitelisting is working
- ✅ API credentials are correct
- ✅ Balance fetching is functional
- ✅ Ready for Step 2 (bot operations)

---

## 🐛 **If Test Fails**

### **1401 Error:**
- Wait 1-2 minutes (IP propagation)
- Verify IPs are whitelisted in Coinstore dashboard
- Check API key permissions

### **Other Errors:**
- Check DATABASE_URL and ENCRYPTION_KEY are set
- Verify credentials exist in database
- Check network connectivity

---

**Ready to test! Run the script on Hetzner and share results.**
