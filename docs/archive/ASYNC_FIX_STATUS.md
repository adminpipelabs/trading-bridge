# Async SQLAlchemy Fix - Status

**Date:** 2026-01-26  
**Issue:** `greenlet_spawn has not been called` error when accessing database in async routes

---

## ✅ **Fix Applied**

**Problem:** Async FastAPI routes using synchronous SQLAlchemy operations directly causes greenlet errors.

**Solution:** Wrap database operations in `run_in_threadpool` from Starlette.

**Files Updated:**
1. `app/clients_routes.py` - `list_clients` route
2. `app/bot_routes.py` - `list_bots` route (partial)

---

## 🔄 **Remaining Work**

**Need to wrap all DB operations in these routes:**

### `app/clients_routes.py`:
- ✅ `list_clients` - Fixed
- ⏳ `create_client` - Needs fix
- ⏳ `get_client` - Needs fix
- ⏳ `get_client_by_wallet` - Needs fix
- ⏳ `add_wallet` - Needs fix
- ⏳ `add_connector` - Needs fix
- ⏳ `delete_client` - Needs fix

### `app/bot_routes.py`:
- ✅ `list_bots` - Fixed
- ⏳ `get_bot` - Needs fix
- ⏳ `create_bot` - Needs fix
- ⏳ `start_bot` - Needs fix
- ⏳ `stop_bot` - Needs fix
- ⏳ `delete_bot` - Needs fix
- ⏳ `get_bot_status` - Needs fix

---

## 🧪 **Test After Fix**

```bash
# Test clients endpoint
curl https://trading-bridge-production.up.railway.app/clients

# Test bots endpoint
curl https://trading-bridge-production.up.railway.app/bots
```

**Expected:** No more `greenlet_spawn` errors

---

## 📝 **Pattern to Follow**

**Before:**
```python
async def my_route(db: Session = Depends(get_db)):
    clients = db.query(Client).all()  # ❌ Direct DB access
    return {"clients": clients}
```

**After:**
```python
async def my_route(db: Session = Depends(get_db)):
    def _get_clients():
        return db.query(Client).all()
    
    clients = await run_in_threadpool(_get_clients)  # ✅ Wrapped
    return {"clients": clients}
```

---

**Status:** Partial fix applied. Need to complete remaining routes.
