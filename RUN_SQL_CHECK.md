# How to Run SQL Check for Sharp's Connectors

## Option 1: Railway PostgreSQL Console (Recommended)

1. **Go to Railway Dashboard:**
   - Open your Railway project
   - Click on the PostgreSQL service
   - Click "Query" tab (or "Connect" → "PostgreSQL")

2. **Run this SQL query:**
   ```sql
   SELECT 
       c.id,
       c.name as connector_name,
       c.memo,
       c.api_key IS NOT NULL as has_api_key,
       c.api_secret IS NOT NULL as has_api_secret,
       cl.account_identifier,
       cl.name as client_name
   FROM connectors c
   LEFT JOIN clients cl ON cl.id = c.client_id
   WHERE cl.account_identifier LIKE '%sharp%'
      OR cl.account_identifier LIKE '%Sharp%'
      OR c.name ILIKE '%bitmart%'
   ORDER BY c.created_at DESC;
   ```

3. **Check the results:**
   - `connector_name` should be exactly `"bitmart"` (lowercase)
   - `memo` should have a value (not NULL, not empty)
   - `has_api_key` and `has_api_secret` should both be `true`

---

## Option 2: Railway CLI

```bash
# Connect to PostgreSQL
railway connect postgres

# Then run the SQL query above
```

---

## Option 3: Python Script (if DATABASE_URL is available)

```bash
# Set DATABASE_URL from Railway
export DATABASE_URL=$(railway variables get DATABASE_URL --json | jq -r '.value')

# Run the check script
python3 check_sharp_connectors_now.py
```

---

## Expected Results

### ✅ **Good Configuration:**
```
connector_name: bitmart
memo: 12345678 (or any non-empty value)
has_api_key: true
has_api_secret: true
```

### ❌ **Bad Configuration (Missing Memo):**
```
connector_name: bitmart
memo: NULL  ← THIS IS THE PROBLEM!
has_api_key: true
has_api_secret: true
```

### ❌ **Bad Configuration (Wrong Name):**
```
connector_name: BitMart  ← Should be lowercase "bitmart"
memo: 12345678
has_api_key: true
has_api_secret: true
```

---

## If Memo is Missing - Fix It:

```sql
-- First, get the connector ID from the query above
-- Then update with the correct BitMart UID:

UPDATE connectors 
SET memo = 'YOUR_BITMART_UID_HERE' 
WHERE id = 'connector-id-from-query-above';
```

**Note:** The BitMart UID is provided when you create API keys on BitMart. It's usually a numeric string like `"12345678"`.

---

## If Name is Wrong - Fix It:

```sql
UPDATE connectors 
SET name = 'bitmart' 
WHERE id = 'connector-id-from-query-above';
```

---

## Share Results

After running the query, share:
1. The `connector_name` value
2. Whether `memo` is NULL or has a value
3. The `has_api_key` and `has_api_secret` values

This will help identify the exact issue!
