# How to Check Sharp's BitMart Connectors

## Option 1: Run SQL Query in Railway PostgreSQL

1. Go to Railway dashboard
2. Select your project → PostgreSQL service
3. Click "Query" tab
4. Copy and paste the queries from `CHECK_CONNECTORS_SQL.sql`
5. Run each query and check results

## Option 2: Run Python Script on Railway

```bash
# SSH into Railway service
railway shell

# Run the check script
python3 check_sharp_connectors_now.py
```

## Option 3: Use Railway CLI to Query Database

```bash
# Get database URL
railway variables

# Connect to database
railway connect postgres

# Then run SQL queries from CHECK_CONNECTORS_SQL.sql
```

## What to Look For

### ✅ **Good Connector:**
- `name` = exactly `"bitmart"` (lowercase, no spaces)
- `memo` = has value (BitMart UID)
- `api_key` = has value
- `api_secret` = has value
- `client_id` = matches Sharp's client ID

### ❌ **Bad Connector (Causes Exchange Not to Initialize):**
- `name` = `NULL`, `"BitMart"`, `"Bitmart"`, `"bitmart "` (wrong case/spacing)
- `memo` = `NULL` or empty string
- `api_key` = `NULL` or missing
- `api_secret` = `NULL` or missing

## Quick Fixes

### Fix Connector Name:
```sql
UPDATE connectors 
SET name = 'bitmart' 
WHERE client_id = (SELECT id FROM clients WHERE account_identifier = 'client_new_sharp_foundation')
  AND name ILIKE '%bitmart%';
```

### Add Memo/UID (if missing):
```sql
UPDATE connectors 
SET memo = 'YOUR_BITMART_UID_HERE' 
WHERE client_id = (SELECT id FROM clients WHERE account_identifier = 'client_new_sharp_foundation')
  AND name = 'bitmart';
```

## Expected Results

After running the query, you should see:
- At least 1 connector row for Sharp's BitMart account
- `name` = `"bitmart"` (exact match)
- `memo` = some value (BitMart UID)
- Both API key and secret present

If you see **NO RESULTS**, that means:
- Connector doesn't exist in `connectors` table
- Need to create it or sync from `exchange_credentials` table
- This is why exchange isn't initializing!
