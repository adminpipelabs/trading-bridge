# Check Sharp's BitMart Balance - Instructions

## ✅ **Option 3: SQL Query in Railway (Recommended)**

### **Step 1: Open Railway PostgreSQL Query Tab**

1. Go to **Railway Dashboard**
2. Click on your **PostgreSQL** service
3. Click on **Query** tab

### **Step 2: Run This SQL Query**

Copy and paste this query:

```sql
-- Find Sharp's client and BitMart connector
SELECT 
    c.id as client_id,
    c.name as client_name,
    c.account_identifier,
    conn.name as exchange,
    LEFT(conn.api_key, 15) || '...' as api_key_preview,
    CASE WHEN conn.api_secret IS NOT NULL THEN '***SET***' ELSE 'MISSING' END as api_secret_status,
    conn.memo as uid_memo,
    conn.created_at as connector_created
FROM clients c
LEFT JOIN connectors conn ON conn.client_id = c.id
WHERE c.name ILIKE '%sharp%' OR c.account_identifier ILIKE '%sharp%'
ORDER BY c.created_at DESC;
```

### **Step 3: Check Results**

**What you'll see:**
- ✅ **If connector exists**: Shows `exchange = bitmart`, `api_key_preview`, `api_secret_status = ***SET***`
- ❌ **If no connector**: Shows `exchange = NULL` or no rows

### **Step 4: Test Balance (If Connector Exists)**

If you see a BitMart connector, you can test the balance using Python:

```python
import ccxt.async_support as ccxt
import asyncio

async def check_balance():
    exchange = ccxt.bitmart({
        'apiKey': 'YOUR_API_KEY_FROM_DB',
        'secret': 'YOUR_API_SECRET_FROM_DB',
        'uid': 'YOUR_MEMO_FROM_DB',  # If memo exists
        'enableRateLimit': True,
    })
    
    await exchange.load_markets()
    balance = await exchange.fetch_balance()
    
    # Show non-zero balances
    for currency, amounts in balance.get("total", {}).items():
        total = float(amounts) if amounts else 0
        if total > 0:
            free = float(balance.get("free", {}).get(currency, 0))
            print(f"{currency}: Total={total}, Free={free}")
    
    await exchange.close()

asyncio.run(check_balance())
```

---

## **Alternative: Get Full API Keys from Database**

If you need the full API keys to test manually:

```sql
-- Replace {client_id} with actual ID from first query
SELECT 
    name,
    api_key,
    api_secret,
    memo
FROM connectors
WHERE client_id = '{client_id}' AND name = 'bitmart';
```

⚠️ **Security Note**: This shows sensitive data. Only run in secure environment.

---

## **Expected Results**

### ✅ **If Everything Works:**
- Query shows BitMart connector exists
- API keys are set
- Balance check shows SHARP and USDT balances

### ❌ **If Connector Missing:**
- Query shows no BitMart connector
- Need to add via admin UI: `PUT /clients/{client_id}/connector`

---

## **Quick Check: Run the SQL Now**

**Copy this and run in Railway PostgreSQL Query tab:**

```sql
SELECT 
    c.name,
    c.account_identifier,
    conn.name as exchange,
    CASE WHEN conn.api_key IS NOT NULL THEN 'YES' ELSE 'NO' END as has_api_key,
    conn.memo
FROM clients c
LEFT JOIN connectors conn ON conn.client_id = c.id AND conn.name = 'bitmart'
WHERE c.name ILIKE '%sharp%'
LIMIT 5;
```

This will quickly show if Sharp has a BitMart connector configured.
