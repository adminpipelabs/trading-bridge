# CTO: Check Railway Logs for 500 Error

**Status:** ✅ CORS Fixed - Request Now Reaches Backend  
**New Issue:** ❌ Backend Returns 500 Internal Server Error

**Date:** February 8, 2026

---

## ✅ **Progress Made**

**Before:** "Failed to fetch" - CORS blocking request  
**Now:** "500 Internal Server Error" - Request reaches backend but crashes

**This is GOOD progress!** CORS is fixed. Now we need to fix the backend crash.

---

## 🔍 **What to Check in Railway Logs**

**Go to Railway Dashboard → `trading-bridge` service → Logs tab**

**Look for errors when this endpoint is called:**
```
POST /bots/{bot_id}/start
```

**Search for:**
1. **Exception/Traceback** - Full Python traceback showing what crashed
2. **Error messages** - Look for:
   - `AttributeError`
   - `TypeError`
   - `KeyError`
   - `ImportError`
   - `DatabaseError`
   - `NameError`

3. **Specific lines to check:**
   - Line 829-867 in `bot_routes.py` (start_bot function)
   - Any `bot_runner` related errors
   - Database query errors
   - Missing imports

---

## 📋 **Common Causes of 500 in start_bot**

**1. Missing bot_runner import:**
```python
# Line 852: await bot_runner.start_bot(bot_id, db)
# If bot_runner is None or not imported, this crashes
```

**2. Database error:**
```python
# Line 832-834: Raw SQL query
bot_check = db.execute(text("""
    SELECT exchange, chain FROM bots WHERE id = :bot_id
"""), {"bot_id": bot_id}).first()
# If column doesn't exist or query fails
```

**3. Bot runner not initialized:**
```python
# bot_runner might be None if not started properly
```

**4. Async/await issue:**
```python
# Line 852: await bot_runner.start_bot(bot_id, db)
# If bot_runner.start_bot is not async or has wrong signature
```

---

## 🔧 **Quick Fixes to Try**

**If bot_runner is None:**
- Check if bot_runner is initialized in `main.py` lifespan
- Verify bot_runner startup logs show "✅ Bot runner started"

**If database column missing:**
- Check if `exchange` column exists in `bots` table
- Run migration if needed

**If import error:**
- Check if `from app.bot_runner import bot_runner` is correct
- Verify bot_runner module exists

---

## 📝 **What to Report**

**After checking Railway logs, share:**
1. **Full traceback** - Copy the entire error stack trace
2. **Error type** - `AttributeError`, `TypeError`, etc.
3. **Line number** - Which line in `bot_routes.py` crashed
4. **Error message** - Exact error message

---

## 🧪 **Test After Fix**

Once fixed, test again:
1. Click "Start Bot" in browser
2. Should get 200 (success) or 401 (auth error), NOT 500
3. Check Railway logs confirm no errors

---

**Check Railway logs NOW and share the traceback!**
