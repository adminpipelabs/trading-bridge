# Fix: Prevent asyncpg Usage in Sync Routes

**Date:** 2026-01-26  
**Issue:** SQLAlchemy trying to use asyncpg (async driver) in sync routes

---

## ❌ **Error**

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
File: sqlalchemy/dialects/postgresql/asyncpg.py
```

**Root Cause:** SQLAlchemy is detecting and using `asyncpg` driver instead of `psycopg2` sync driver.

---

## ✅ **Fix Applied**

**Updated `app/database.py`:**
1. Force `postgresql+psycopg2://` URL format
2. Remove any `+asyncpg` references
3. Add explicit sync driver check
4. Add connection timeout

**Changes:**
- Ensure URL always uses `+psycopg2` driver
- Replace `+asyncpg` if present
- Log the URL being used (first 50 chars)

---

## 🧪 **Test After Deployment**

```bash
curl https://trading-bridge-production.up.railway.app/bots
curl https://trading-bridge-production.up.railway.app/clients
```

**Expected:** Should work without greenlet errors.

---

**Fix pushed. Waiting for deployment.** 🚀
