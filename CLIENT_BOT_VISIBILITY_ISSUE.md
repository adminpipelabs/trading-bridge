# Client Bot Visibility Issue - Need Dev Help

**Date:** 2026-01-26  
**Issue:** Client sees "No bots configured" even though admin created bot with `account: "client_sharp"`

---

## ✅ **What We've Implemented**

### **Backend (`trading-bridge`)**
1. ✅ Added account filtering to `/bots` endpoint
   - Accepts `?account=client_sharp` query parameter
   - Filters bots by `account` field in bot metadata

2. ✅ Bot creation stores account identifier
   - When admin creates bot, `account` field is stored in `bot_metadata`
   - Example: `{"account": "client_sharp", ...}`

### **Frontend (`ai-trading-ui`)**
1. ✅ Updated `BotList` component
   - Accepts `account` prop
   - Filters bots by account when provided
   - Falls back to showing all bots if no account filter

2. ✅ Added BotList to ClientDashboard
   - Shows "My Bots" section in client view
   - Currently hardcoded to use `client_sharp` account

---

## ❌ **Current Problem**

**Client sees:** "No bots configured"  
**Admin created:** Bot with `account: "client_sharp"`  
**Client wallet:** `0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685`

**Root cause:** Account mapping issue
- Client dashboard hardcoded to use `client_sharp`
- No proper mapping from wallet address → account identifier
- Need to know: How does wallet address map to account identifier?

---

## 🔍 **Questions for Dev**

### **1. Account Identifier Mapping**
**How should we map wallet address to account identifier?**

**Current situation:**
- Admin creates client with wallet: `0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685`
- Admin creates bot with: `account: "client_sharp"`
- Client logs in with wallet: `0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685`
- Client needs to see bots for: `account: "client_sharp"`

**Options:**
- **Option A:** Backend stores account identifier in client/user record
  - Client record has `account_identifier` field
  - Frontend fetches from `/api/clients/me` or similar
  - Use that to filter bots

- **Option B:** Use wallet address hash as account identifier
  - Derive account from wallet: `client_${wallet.slice(2,10)}`
  - Admin must use same pattern when creating bots

- **Option C:** Backend provides mapping endpoint
  - `/api/clients/{client_id}/account` returns account identifier
  - Frontend uses that to filter bots

**Which approach do you prefer?**

---

### **2. Client Account Storage**
**Where is the client's account identifier stored?**

**Current code:**
```javascript
// Hardcoded in ClientDashboard
setClientAccount('client_sharp'); // ❌ Hardcoded
```

**What we need:**
```javascript
// Should fetch from backend
const clientInfo = await clientAPI.getMyAccount();
setClientAccount(clientInfo.account_identifier); // ✅ From backend
```

**Does the backend have:**
- Client/user record with `account_identifier` field?
- Endpoint to get client's account identifier?
- Mapping table: wallet_address → account_identifier?

---

### **3. Bot Creation Account Field**
**When admin creates bot, what account value should be used?**

**Current flow:**
1. Admin selects client (has wallet: `0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685`)
2. Admin creates bot with `account: "client_sharp"`
3. Bot stored with `account: "client_sharp"` in metadata

**Questions:**
- Should admin manually enter account identifier?
- Or should it be auto-filled from client record?
- What's the correct account identifier for wallet `0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685`?

---

## 🛠️ **Proposed Solution**

### **Option 1: Backend Stores Account Identifier**
```python
# In client/user record
{
  "id": 123,
  "wallet_address": "0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685",
  "account_identifier": "client_sharp",  # ← Add this field
  ...
}
```

**Frontend:**
```javascript
// Fetch client info
const clientInfo = await clientAPI.getMyInfo();
setClientAccount(clientInfo.account_identifier);

// Filter bots
<BotList account={clientAccount} />
```

---

### **Option 2: Derive from Wallet Address**
```javascript
// Consistent pattern
const accountIdentifier = `client_${walletAddress.slice(2, 10).toLowerCase()}`;
// For 0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685
// → client_6cc52d4b
```

**Requires:**
- Admin uses same pattern when creating bots
- Or backend normalizes account identifier

---

### **Option 3: Use Client ID**
```javascript
// Use client ID as account identifier
const accountIdentifier = `client_${user.id}`;
// For client ID 1 → client_1
```

**Requires:**
- Admin uses `client_${clientId}` when creating bots
- Consistent naming convention

---

## 📋 **What We Need**

1. **Clarification:**
   - How should wallet address map to account identifier?
   - Where is this mapping stored?

2. **Backend Endpoint (if needed):**
   ```python
   GET /api/clients/me
   # Returns: { "account_identifier": "client_sharp", ... }
   ```

3. **Database Schema (if needed):**
   ```sql
   ALTER TABLE clients ADD COLUMN account_identifier VARCHAR;
   ```

4. **Testing:**
   - What account identifier should be used for wallet `0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685`?
   - Verify bot was created with correct account identifier

---

## 🔧 **Current Code Locations**

**Backend:**
- `trading-bridge/app/bot_routes.py` - `/bots?account=...` endpoint
- `trading-bridge/app/bot_routes.py` - Bot creation stores `account` field

**Frontend:**
- `ai-trading-ui/src/components/BotList.jsx` - Accepts `account` prop
- `ai-trading-ui/src/pages/AdminDashboard.jsx` - ClientDashboard hardcodes `client_sharp`

---

## ✅ **What Works**

- ✅ Admin can create bots
- ✅ Admin can see all bots in Bot Management
- ✅ Backend filters bots by account
- ✅ Frontend BotList component filters by account
- ✅ Client dashboard shows "My Bots" section

## ❌ **What Doesn't Work**

- ❌ Client doesn't see their bots (account mapping issue)
- ❌ Account identifier is hardcoded instead of fetched from backend

---

**Please advise on:**
1. How to map wallet address to account identifier
2. Where account identifier should be stored
3. How frontend should fetch client's account identifier

**Once we have this, we can:**
- Update ClientDashboard to fetch account from backend
- Ensure bot creation uses correct account identifier
- Test end-to-end: Admin creates bot → Client sees bot

---

**Ready to implement once we have the mapping strategy!** 🚀
