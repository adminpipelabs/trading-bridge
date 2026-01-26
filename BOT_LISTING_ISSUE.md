# Bot Listing Issue - Bots Not Showing in UI

**Date:** 2026-01-26  
**Issue:** Bot creation works, but bots don't appear in Bot Management page

---

## 🔍 **Problem**

**UI shows:** Empty bot list  
**Bot creation:** ✅ Works (bot created successfully)  
**API endpoint:** `/bots` returns `{"bots": []}`

---

## 📋 **Findings**

### **1. Hummingbot Status Endpoint**
```bash
curl -u admin:admin -H "ngrok-skip-browser-warning: true" \
  https://...ngrok.../bot-orchestration/status
```

**Returns:** `{"status":"success","data":{}}`  
**Issue:** Empty `data` - no bots listed

### **2. Bot Creation**
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/bots/create" \
  -d '{"name":"Sharp Spread",...}'
```

**Returns:** ✅ Success - Bot created  
**Bot stored in:** `self.bot_metadata` (local cache)

### **3. Bot Listing Code**
```python
async def list_bots(self):
    status = await self.hummingbot_client.get_status()
    bots_data = status.get("bots", {})  # Empty!
    # ...
    return {"bots": bots}
```

**Issue:** Looking for `status.get("bots", {})` but Hummingbot returns `{"status":"success","data":{}}`

---

## ✅ **Fix Applied**

Updated `list_bots` to:
1. Check `status.get("data", {}).get("bots", {})` structure
2. Include bots from local metadata (`self.bot_metadata`)
3. Merge Hummingbot status with local cache

---

## ❓ **Questions for Dev**

1. **What does `/bot-orchestration/status` return?**
   - Should it return bots in `data.bots`?
   - Or should we use `/bot-orchestration/bot-runs` instead?

2. **Bot-runs endpoint:**
   - Returns JSON with bot data
   - Should we use this for listing bots?
   - What's the correct structure?

3. **Local metadata:**
   - Bots are stored in `self.bot_metadata` after creation
   - Should we rely on this, or always query Hummingbot?

---

## 🛠️ **Possible Solutions**

### **Option 1: Use bot-runs endpoint**
```python
bot_runs = await self.hummingbot_client.get_bot_runs()
# Parse bot_runs to get bot list
```

### **Option 2: Fix status endpoint parsing**
```python
status = await self.hummingbot_client.get_status()
bots_data = status.get("data", {}).get("bots", {})
```

### **Option 3: Rely on local metadata**
```python
# Return bots from self.bot_metadata
return {"bots": list(self.bot_metadata.values())}
```

---

## 📊 **Current State**

- ✅ Bot creation works
- ✅ Bots stored in local metadata
- ❌ Bot listing returns empty (Hummingbot status empty)
- ❓ Need to verify correct endpoint/structure

---

**Please advise on correct endpoint and data structure for listing bots!** 🔍
