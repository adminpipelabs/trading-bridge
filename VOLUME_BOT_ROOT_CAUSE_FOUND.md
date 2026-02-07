# Volume Bot Root Cause - FOUND ✅

## Test Results

**Test Volume Bot Insert**: ✅ SUCCESS
- Created via `/bots/debug/test-volume-bot-insert` endpoint
- Appears in database: `Sharp-VB-BitMart-Test` (bot_type="volume")
- **Appears in UI**: ✅ User confirmed they can see it

## Conclusion

✅ **Database can handle volume bots**  
✅ **UI can display volume bots**  
❌ **Problem is in backend creation logic** when creating via `/clients/{client_id}/setup-bot` endpoint

## What This Means

The issue is **specifically in the wizard creation flow**. When user clicks "Create & Start Bot" for a volume bot:
- Frontend sends correct request ✅
- Backend receives request ✅
- Backend returns success ✅
- **But bot is NOT saved to database** ❌

## Next Steps

### 1. Check Railway Logs
When volume bot is created via wizard, look for:
- Does it reach `db.add(bot)`?
- Does `db.flush()` succeed?
- Does `db.commit()` succeed?
- Any rollback happening?

### 2. Compare Execution Paths
Check if there's a difference in how volume vs spread bots are handled:
- Config merging logic
- Transaction commits
- Error handling

### 3. Most Likely Issue
**Transaction rollback** - Bot is created but transaction is rolled back due to:
- Error in UPDATE statement for exchange/chain fields
- Error in background task creation
- Exception after bot creation but before commit

## Files to Check

- `app/client_setup_routes.py` - `setup_bot()` function
- Look for differences in execution path between volume and spread bots
- Check all `db.commit()` and `db.rollback()` calls
