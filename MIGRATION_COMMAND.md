# Run Migrations — Quick Command

## ✅ **Easiest Method: Railway CLI**

Run this single command from the project directory:

```bash
cd /Users/mikaelo/trading-bridge
railway run python railway_migrate.py
```

This will:
1. ✅ Use DATABASE_URL from Railway environment automatically
2. ✅ Run all migrations from `migrations/COMPLETE_SETUP.sql`
3. ✅ Show progress and verify results
4. ✅ Handle harmless errors (IF NOT EXISTS, etc.)

---

## 🔧 **Alternative: Direct SQL Execution**

If the Python script doesn't work, you can also run SQL directly:

```bash
railway connect postgres
```

Then in the psql prompt:
```sql
\i migrations/COMPLETE_SETUP.sql
```

Or copy-paste the SQL file contents.

---

## 📋 **What Gets Created**

After running migrations:

1. **Bot Health Columns:**
   - `health_status`, `reported_status`, `last_trade_time`, etc.

2. **Trading Keys Table:**
   - `trading_keys` table for encrypted key storage

3. **Health Logs Table:**
   - `bot_health_logs` table for health check history

4. **Client Roles Fixed:**
   - All clients set to 'client' role
   - Admin set to 'admin' role

---

## ✅ **Verify After Running**

```bash
railway run python -c "
import os
import psycopg2
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL')
parsed = urlparse(db_url)
conn = psycopg2.connect(
    host=parsed.hostname,
    port=parsed.port or 5432,
    database=parsed.path[1:],
    user=parsed.username,
    password=parsed.password,
)
cursor = conn.cursor()
cursor.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'bots' AND column_name = 'health_status'\")
print('✅ health_status exists' if cursor.fetchone() else '❌ Missing')
cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_name = 'trading_keys'\")
print('✅ trading_keys exists' if cursor.fetchone() else '❌ Missing')
"
```

---

**Run:** `railway run python railway_migrate.py`
