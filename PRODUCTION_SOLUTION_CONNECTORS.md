# Production Solution: Connector Management

## Current State

- ✅ Endpoints exist to query BitMart (`/api/exchange/dashboard/{account}`)
- ✅ Auto-sync function loads connectors from DB → `exchange_manager`
- ❌ **Sharp Foundation has NO connectors in `trading-bridge` database**

## Production Solution

### **Option 1: Admin Adds Connectors via UI (Recommended)**

When admin creates/manages clients, connectors should be added to `trading-bridge` database.

**Flow**:
1. Admin logs in → Clients → Sharp Foundation
2. Admin clicks "Add API Key" / "Add Connector"
3. Enters BitMart credentials:
   - Exchange: `bitmart`
   - API Key: `...`
   - API Secret: `...`
   - Memo: `...`
4. Frontend calls: `PUT /clients/{client_id}/connector`
5. Backend saves to PostgreSQL `connectors` table
6. Dashboard endpoints automatically use these connectors

**Status**: ✅ Endpoint exists (`PUT /clients/{client_id}/connector`)

---

### **Option 2: Auto-Sync on Client Creation**

When admin creates a client with connectors, automatically save them to `trading-bridge` DB.

**Current**: `POST /clients/create` accepts `connectors` array but may not be used by frontend.

**Fix Needed**: Ensure frontend passes connectors when creating clients.

---

### **Option 3: Sync from Hummingbot (If Keys Only There)**

If connectors only exist in Hummingbot credentials profiles, create a sync script.

**Implementation**:
```python
# app/sync_connectors.py
async def sync_connectors_from_hummingbot(account_identifier: str):
    """
    Read connectors from Hummingbot credentials profile
    and save to trading-bridge database.
    """
    # 1. Query Hummingbot API for credentials profile
    # 2. Parse connector configs (bitmart.yml, etc.)
    # 3. Save to trading-bridge DB
```

**When to use**: Only if connectors are NOT in trading-bridge DB and only in Hummingbot.

---

## Recommended Production Flow

### **Step 1: Add Connectors via Admin UI**

1. **Admin logs in** → Navigate to Clients
2. **Select "Sharp Foundation"** → Click "API Keys" tab
3. **Click "Add API Key"** → Fill form:
   ```
   Exchange: bitmart
   API Key: [from BitMart]
   API Secret: [from BitMart]
   Memo: [from BitMart]
   ```
4. **Submit** → Connector saved to `trading-bridge` DB

### **Step 2: Verify Connector Added**

```bash
curl https://trading-bridge-production.up.railway.app/clients
# Should show "connectors": [{"name": "bitmart", ...}]
```

### **Step 3: Test Dashboard**

```bash
curl https://trading-bridge-production.up.railway.app/api/exchange/dashboard/client_sharp
# Should return real balances, trades, P&L
```

---

## Implementation Checklist

- [x] Endpoint exists: `PUT /clients/{client_id}/connector`
- [x] Endpoint exists: `GET /api/exchange/dashboard/{account}`
- [x] Auto-sync function: `sync_connectors_to_exchange_manager()`
- [ ] **Frontend UI**: Admin can add connectors via "Add API Key" button
- [ ] **Verify**: Connectors appear in `/clients` response
- [ ] **Test**: Dashboard shows real data

---

## Quick Fix: Add Connector via API

If admin UI isn't ready, add connector directly via API:

```bash
# 1. Get client ID
CLIENT_ID=$(curl -s https://trading-bridge-production.up.railway.app/clients | \
  python3 -c "import sys, json; \
    data=json.load(sys.stdin); \
    client=[c for c in data if c['name']=='Sharp Foundation'][0]; \
    print(client['id'])")

# 2. Add BitMart connector
curl -X PUT \
  "https://trading-bridge-production.up.railway.app/clients/$CLIENT_ID/connector" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bitmart",
    "api_key": "YOUR_BITMART_API_KEY",
    "api_secret": "YOUR_BITMART_API_SECRET",
    "memo": "YOUR_BITMART_MEMO"
  }'
```

---

## Summary

**Production Solution**: 
1. **Admin adds connectors via UI** when managing clients
2. Connectors stored in `trading-bridge` PostgreSQL database
3. Dashboard endpoints automatically use connectors from DB
4. No Hummingbot sync needed (connectors managed in trading-bridge)

**Next Step**: Verify admin UI has "Add API Key" functionality, or add connector via API.
