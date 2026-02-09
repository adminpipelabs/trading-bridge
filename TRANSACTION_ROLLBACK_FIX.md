# Fixed: Database Transaction Rollback Error

**Error:** `PendingRollbackError: This Session's transaction has been rolled back due to a previous exception`

**Date:** February 8, 2026

---

## 🔍 **Root Cause**

**Problem:**
1. SQL query `SELECT exchange, chain FROM bots` fails (columns don't exist)
2. PostgreSQL aborts the transaction
3. Code tries to `db.commit()` later without rolling back first
4. SQLAlchemy throws `PendingRollbackError`

**Error Chain:**
```
SQL Error → Transaction Aborted → Try to Commit → PendingRollbackError
```

---

## ✅ **Fix Applied**

**Added `db.rollback()` after SQL error:**

```python
try:
    bot_check = db.execute(text("""
        SELECT exchange, chain FROM bots WHERE id = :bot_id
    """), {"bot_id": bot_id}).first()
    # ... process result
except Exception as sql_error:
    db.rollback()  # ← Added this
    logger.warning(f"Could not check exchange/chain columns: {sql_error}")
    # Continue with exchange=None, chain=None
```

**Why:** When a SQL query fails, PostgreSQL aborts the transaction. We must rollback before continuing, otherwise any subsequent `db.commit()` will fail.

---

## 📋 **What This Fixes**

**Before:**
- SQL query fails → Transaction aborted
- Try to commit → `PendingRollbackError` → 500 error

**After:**
- SQL query fails → Rollback transaction
- Continue normally → Set bot status → Commit succeeds

---

## 🧪 **Test After Deploy**

1. Click "Start Bot" on BitMart bot
2. Should work now (even if exchange/chain columns don't exist)
3. Bot status should change to "running"
4. No more 500 errors

---

**Status:** ✅ Fixed and deployed
