# Hummingbot Integration - Implementation Plan

**For Developer Review**

---

## 🎯 **What We're Doing**

Connect Trading Bridge bot endpoints to Hummingbot API so bots actually execute trades instead of just storing data in memory.

**Current State:**
- ✅ Bot endpoints exist (`/bots`, `/bots/create`, `/bots/{id}/start`, etc.)
- ✅ BotManager stores bots in memory (stub)
- ❌ Bots don't actually connect to Hummingbot
- ❌ No real trading happens

**After Implementation:**
- ✅ Bot endpoints call Hummingbot API
- ✅ Bots are created/started/stopped in Hummingbot
- ✅ Real trading happens
- ✅ Bot status reflects Hummingbot state

---

## 📁 **Files I'll Create/Modify**

### **NEW FILE: `app/hummingbot_client.py`**
HTTP client for Hummingbot API communication

**What it does:**
- Handles authentication (basic auth)
- Makes HTTP requests to Hummingbot endpoints
- Returns Python dicts
- Handles errors gracefully

**Key Methods:**
```python
- get_status() → Get all running bots
- start_bot(bot_name, script_file, config) → Start a bot
- stop_bot(bot_name) → Stop a bot
- deploy_script(script_content, script_name) → Deploy strategy script
- get_bot_history(bot_name) → Get trade history
```

---

### **MODIFY: `app/bot_routes.py`**

**Current Code:**
- `BotManager` stores bots in memory dict
- Endpoints return mock data

**What I'll Change:**

1. **Import HummingbotClient**
   ```python
   from app.hummingbot_client import HummingbotClient
   ```

2. **Initialize client**
   ```python
   hummingbot_client = HummingbotClient()
   ```

3. **Update `BotManager.list_bots()`**
   - Currently: Returns `self.bots` dict
   - After: Calls `hummingbot_client.get_status()`
   - Transforms Hummingbot format to our format

4. **Update `BotManager.create_bot()`**
   - Currently: Stores in memory dict
   - After: 
     - Generates Hummingbot script
     - Calls `hummingbot_client.deploy_script()`
     - Calls `hummingbot_client.start_bot()`
     - Stores bot metadata (for reference)

5. **Update `BotManager.start_bot()`**
   - Currently: Sets status to "running" in dict
   - After: Calls `hummingbot_client.start_bot()`

6. **Update `BotManager.stop_bot()`**
   - Currently: Sets status to "stopped" in dict
   - After: Calls `hummingbot_client.stop_bot()`

7. **Add script generation function**
   - Takes strategy, connector, pair, config
   - Returns Hummingbot v2 script as string

---

## 🔧 **Technical Details**

### **HummingbotClient Implementation**

```python
import httpx
import os

class HummingbotClient:
    def __init__(self):
        self.base_url = os.getenv("HUMMINGBOT_API_URL", "http://localhost:8000")
        self.username = os.getenv("HUMMINGBOT_API_USERNAME", "hummingbot")
        self.password = os.getenv("HUMMINGBOT_API_PASSWORD", "")
        self.auth = (self.username, self.password)
    
    async def _request(self, method: str, endpoint: str, **kwargs):
        """Make authenticated HTTP request"""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method, url, auth=self.auth, **kwargs
            )
            response.raise_for_status()
            return response.json()
    
    async def get_status(self):
        """GET /bot-orchestration/status"""
        return await self._request("GET", "/bot-orchestration/status")
    
    async def start_bot(self, bot_name: str, script_file: str, config: dict):
        """POST /bot-orchestration/start-bot"""
        return await self._request(
            "POST",
            "/bot-orchestration/start-bot",
            json={
                "bot_name": bot_name,
                "script_file": script_file,
                "config": config
            }
        )
    
    # ... other methods
```

---

### **Script Generation**

**Function:** `generate_hummingbot_script(strategy, connector, pair, config)`

**For "spread" strategy:**
```python
from hummingbot.strategy.pure_market_making.pure_market_making_v2 import PureMarketMakingStrategyV2

strategy = PureMarketMakingStrategyV2(
    exchange="bitmart",
    trading_pair="SHARP/USDT",
    bid_spread=0.001,
    ask_spread=0.001,
    order_amount=100,
    order_refresh_time=60
)
```

**For "volume" strategy:**
- Will need custom script (TBD based on requirements)

---

### **Data Transformation**

**Hummingbot Format:**
```json
{
  "bots": {
    "bot_name": {
      "is_running": true,
      "strategy": "pure_market_making",
      "connector": "bitmart",
      "trading_pair": "SHARP/USDT"
    }
  }
}
```

**Our Format:**
```json
{
  "bots": [
    {
      "id": "bot_name",
      "name": "bot_name",
      "status": "running",
      "strategy": "spread",
      "connector": "bitmart",
      "pair": "SHARP/USDT",
      "chain": "evm"
    }
  ]
}
```

**Transformation Logic:**
- `is_running` → `status: "running"` or `"stopped"`
- `strategy` → Map to our strategy names
- `connector` → Check if "jupiter" → `chain: "solana"`, else `chain: "evm"`

---

## 🔐 **Environment Variables**

**Required in Railway (Trading Bridge service):**

```bash
HUMMINGBOT_API_URL=http://localhost:8000  # Or Tailscale IP
HUMMINGBOT_API_USERNAME=hummingbot
HUMMINGBOT_API_PASSWORD=<password>
```

**How to set:**
1. Railway dashboard → Trading Bridge service
2. Variables tab
3. Add these three variables
4. Redeploy

---

## 🧪 **Testing Plan**

### **Step 1: Test HummingbotClient**
```python
# Test script
import asyncio
from app.hummingbot_client import HummingbotClient

async def test():
    client = HummingbotClient()
    status = await client.get_status()
    print(status)

asyncio.run(test())
```

### **Step 2: Test Endpoints**
```bash
# Get bots (should return Hummingbot bots)
curl http://localhost:8080/bots

# Create bot
curl -X POST http://localhost:8080/bots/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_bot",
    "strategy": "spread",
    "connector": "bitmart",
    "pair": "SHARP/USDT",
    "account": "client_sharp",
    "config": {}
  }'
```

### **Step 3: Verify in Hummingbot**
- Check Hummingbot UI/logs
- Verify bot is running
- Check trades are happening

---

## ⚠️ **Potential Issues**

### **Issue 1: Network Connectivity**
**Problem:** Railway can't reach local Hummingbot  
**Solution:** Use Tailscale VPN or deploy Hummingbot to Railway

### **Issue 2: Script Format**
**Problem:** Generated script doesn't match Hummingbot v2 format  
**Solution:** Test with simple script, iterate based on errors

### **Issue 3: Authentication**
**Problem:** Hummingbot API rejects requests  
**Solution:** Verify credentials, check auth method

### **Issue 4: Bot Naming**
**Problem:** Bot name conflicts  
**Solution:** Add timestamp or UUID to bot names

---

## 📊 **Data Flow**

### **Create Bot:**
```
1. POST /bots/create
   ↓
2. BotManager.create_bot()
   ↓
3. generate_hummingbot_script()
   ↓
4. hummingbot_client.deploy_script()
   ↓
5. hummingbot_client.start_bot()
   ↓
6. Return success
```

### **List Bots:**
```
1. GET /bots
   ↓
2. BotManager.list_bots()
   ↓
3. hummingbot_client.get_status()
   ↓
4. Transform format
   ↓
5. Return bots list
```

---

## ✅ **What Success Looks Like**

1. ✅ `/bots` returns real bots from Hummingbot
2. ✅ `/bots/create` creates and starts bots in Hummingbot
3. ✅ `/bots/{id}/start` starts bots in Hummingbot
4. ✅ `/bots/{id}/stop` stops bots in Hummingbot
5. ✅ Bot status reflects Hummingbot state
6. ✅ Errors are handled gracefully

---

## 💬 **Questions for You**

1. **Script Format:**
   - Do you have existing Hummingbot script templates?
   - What's the exact format for v2 scripts?
   - Any required config parameters?

2. **Strategy Mapping:**
   - How do our strategies map to Hummingbot strategies?
   - "spread" → `PureMarketMakingStrategyV2`?
   - "volume" → Custom script?

3. **Error Handling:**
   - How should we handle Hummingbot API errors?
   - Should we retry on failures?
   - What error format should we return?

4. **Bot Persistence:**
   - Should we still store bot metadata in BotManager?
   - Or rely entirely on Hummingbot?

5. **Testing:**
   - Do you have a test Hummingbot instance?
   - Should I test locally first?

---

## 🚀 **Implementation Steps**

1. **Create HummingbotClient** (`app/hummingbot_client.py`)
2. **Add script generation function** (in `bot_routes.py`)
3. **Update BotManager methods** (in `bot_routes.py`)
4. **Test locally** (if possible)
5. **Deploy to Railway**
6. **Set environment variables**
7. **Test end-to-end**

---

## 📝 **Review Checklist**

Before I start, please confirm:

- [ ] You've reviewed this plan
- [ ] You have feedback/questions
- [ ] Hummingbot API is accessible
- [ ] Credentials are available
- [ ] Network connectivity is set up

---

**Ready for your feedback!** 🚀
