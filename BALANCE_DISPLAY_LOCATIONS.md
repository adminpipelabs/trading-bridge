# Where Balances Should Be Displayed

## 📊 **Client Dashboard** (Client sees their own balance)

**Location:** Client logs in → Overview tab → **"WALLET BALANCE"** card

**API Endpoint Used:**
```
GET /api/clients/portfolio?wallet_address=0x...
```

**What It Shows:**
- Total USD value
- Individual token balances (SHARP, USDT, etc.)
- Bot counts (active/total)

**Current Status:** ❌ Showing **"-"** (empty)

**Fix:** The logging fix I just deployed should help diagnose why it's failing.

---

## 👨‍💼 **Admin Dashboard** (Admin sees any client's balance)

**Location:** Admin logs in → Clients → Select Client → **Balances** tab/section

**API Endpoint Used:**
```
GET /admin/clients/{client_id}/balances
```

**What It Shows:**
- Client name
- All token balances (SHARP, USDT, etc.)
- Total USD value
- Token count

**Current Status:** ❓ Unknown (need to test)

**Fix:** Uses same sync logic, so same fix applies.

---

## 🔍 **Both Use Same Backend Logic**

Both endpoints:
1. ✅ Look up client
2. ✅ Sync connectors from DB → `exchange_manager`
3. ✅ Query BitMart API via `ccxt`
4. ✅ Return balances

**The issue:** Connectors aren't syncing or balance fetch is failing.

---

## ✅ **What Should Happen**

### **Client Dashboard:**
```
WALLET BALANCE
$1,500.00

Tokens:
• 8,000,000 SHARP
• 1,500 USDT
```

### **Admin Dashboard:**
```
Client: New Sharp Foundation
Total USD: $1,500.00

Balances:
• BitMart: 8,000,000 SHARP (Free: 8,000,000)
• BitMart: 1,500 USDT (Free: 1,500)
```

---

## 🚨 **Current Problem**

**Both dashboards showing empty because:**
1. Connectors not syncing (no API keys in `exchange_manager`)
2. Balance fetch failing (API error, invalid keys, etc.)
3. No error messages shown to user

---

## 🔧 **Fix Deployed**

**What I just fixed:**
- ✅ Added comprehensive logging to sync process
- ✅ Better error messages
- ✅ Diagnostic endpoint: `/api/clients/debug?wallet_address=...`

**Next Steps:**
1. Check Railway logs after deployment
2. Test both endpoints
3. Fix based on what logs show

---

## 📋 **Testing Checklist**

### **Test Client Dashboard:**
```bash
# Get Sharp's wallet address first
curl "https://trading-bridge-production.up.railway.app/api/clients/portfolio?wallet_address=WALLET_ADDRESS" | jq
```

### **Test Admin Dashboard:**
```bash
# Get Sharp's client_id first
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  "https://trading-bridge-production.up.railway.app/admin/clients/{client_id}/balances" | jq
```

### **Test Debug Endpoint:**
```bash
curl "https://trading-bridge-production.up.railway.app/api/clients/debug?wallet_address=WALLET_ADDRESS" | jq
```

---

## 🎯 **Answer: BOTH**

**Balances should appear in:**
- ✅ **Client Dashboard** - Client sees their own balance
- ✅ **Admin Dashboard** - Admin sees any client's balance

**Both are currently broken** because connectors aren't syncing properly.

**The fix I deployed will help diagnose and fix both.**
