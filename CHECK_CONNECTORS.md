# Connector Check Results

## Current Status

### `/clients` Endpoint Response:
```json
{
  "clients": [{
    "id": "70ab29b1-66ad-4645-aec8-fa2f55abe144",
    "name": "Sharp Foundation",
    "account_identifier": "client_sharp",
    "connectors": []  // ❌ EMPTY!
  }]
}
```

**Result**: Sharp Foundation has **0 connectors** in `trading-bridge` database.

---

## Next Steps Needed

### Option 1: Check Database Directly (Railway PostgreSQL)

Run this SQL query in Railway PostgreSQL to see if connectors exist:

```sql
-- Check all connectors
SELECT * FROM connectors;

-- Check if connector is linked to Sharp Foundation client
SELECT 
    c.name as client_name,
    c.account_identifier,
    c.id as client_id,
    conn.id as connector_id,
    conn.name as exchange,
    CASE WHEN conn.api_key IS NOT NULL THEN 'YES' ELSE 'NO' END as has_api_key,
    CASE WHEN conn.api_secret IS NOT NULL THEN 'YES' ELSE 'NO' END as has_api_secret
FROM clients c
LEFT JOIN connectors conn ON c.id = conn.client_id
WHERE c.account_identifier = 'client_sharp';
```

**Expected Results**:
- If connectors exist but wrong `client_id`: Will show connectors but not linked
- If connectors don't exist: Will show NULL for connector fields
- If connectors exist and linked: Will show connector data

---

### Option 2: Add Connector via API

If connectors don't exist, add them:

```bash
# Client ID from /clients response
CLIENT_ID="70ab29b1-66ad-4645-aec8-fa2f55abe144"

# Add BitMart connector
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

### Option 3: Check if Connectors in Hummingbot Only

If connectors only exist in Hummingbot credentials profiles:
- They need to be synced to `trading-bridge` database
- Or we need a sync script to copy them

---

## Summary

**Current State**: 
- ✅ Client exists: Sharp Foundation (`client_sharp`)
- ❌ Connectors: **0 connectors** in database
- ❌ Result: Dashboard shows empty data

**Action Needed**:
1. **Check database** - Run SQL query to see if connectors exist elsewhere
2. **Add connector** - If missing, add via API or admin UI
3. **Verify** - After adding, check `/clients` endpoint shows connector

---

## Files to Check

- `app/clients_routes.py` line 161 - Returns connectors from `client.connectors` relationship
- Database query uses `joinedload(Client.connectors)` - Should load connectors if they exist

**If connectors exist in DB but not showing**: Check `client_id` foreign key matches client `id`.
