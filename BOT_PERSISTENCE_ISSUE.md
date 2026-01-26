# Bot Persistence Issue - Bots Disappearing After Restart

**Date:** 2026-01-26  
**Issue:** Bot created for "Sharp" client is no longer visible in Bot Management after service restart

---

## ❌ **Problem**

**Before:**
- Admin created bot with `account: "client_sharp"`
- Bot was visible in Bot Management
- Bot was running/stopped with Edit button

**After (now):**
- Bot no longer visible in Bot Management
- No Running/Stopped status
- No Edit button
- Client can't see bot configuration

---

## 🔍 **Root Cause**

**Current Implementation:**
```python
# In bot_routes.py
class BotManager:
    def __init__(self, exchange_manager):
        self.bot_metadata = {}  # ❌ In-memory storage
```

**Issue:**
- `bot_metadata` is stored in **memory only**
- When Railway redeploys or service restarts → `bot_metadata` is **lost**
- Bot definitions are **not persisted** to database
- Only bots currently running in Hummingbot would be visible (via `/status` endpoint)

---

## 📋 **Current Architecture**

```
┌─────────────────────────────────────────────────┐
│           Bot Storage Layers                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. bot_metadata (in-memory)                   │
│     ❌ Lost on restart                          │
│     ✅ Fast access                              │
│                                                 │
│  2. Hummingbot API (/status)                   │
│     ✅ Only running bots                        │
│     ❌ No stopped bot definitions               │
│                                                 │
│  3. Database (PostgreSQL)                       │
│     ❌ Not implemented                          │
│     ✅ Would persist across restarts            │
└─────────────────────────────────────────────────┘
```

---

## ✅ **What We Need**

### **Option 1: Database Persistence (Recommended)**

Store bot definitions in PostgreSQL:

```python
# Schema
CREATE TABLE bots (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    account_identifier VARCHAR NOT NULL,
    strategy VARCHAR NOT NULL,
    connector VARCHAR NOT NULL,
    pair VARCHAR NOT NULL,
    config JSONB,
    status VARCHAR DEFAULT 'stopped',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Benefits:**
- ✅ Persists across restarts
- ✅ Can query by account
- ✅ Full bot history
- ✅ Production-ready

---

### **Option 2: Hybrid Approach**

1. **Database** for bot definitions (source of truth)
2. **Hummingbot API** for runtime status (is it running?)
3. **Merge** both when listing bots

```python
async def list_bots(self):
    # 1. Get bot definitions from database
    bots = await db.get_bots(account=account)
    
    # 2. Get runtime status from Hummingbot
    hb_status = await self.hummingbot_client.get_status()
    
    # 3. Merge: Update status for running bots
    for bot in bots:
        if bot.name in running_instances:
            bot.status = "running"
    
    return {"bots": bots}
```

---

## 🛠️ **Quick Fix (Temporary)**

**Restore bot manually:**

1. **Check if bot exists in Hummingbot:**
   ```bash
   curl -u admin:admin -H "ngrok-skip-browser-warning: true" \
     https://...ngrok.../bot-orchestration/status
   ```

2. **If bot exists but not in metadata:**
   - Re-create bot via UI (will add to metadata)
   - Or manually add to `bot_metadata` via API

3. **If bot doesn't exist:**
   - Bot was lost completely
   - Need to recreate from scratch

---

## 📊 **Current State**

| Component | Status | Persistence |
|-----------|--------|-------------|
| `bot_metadata` | ❌ Lost on restart | In-memory only |
| Hummingbot API | ✅ Running bots only | Persistent |
| Database | ❌ Not implemented | N/A |

---

## ❓ **Questions for Dev**

1. **Should we implement database persistence?**
   - Use existing PostgreSQL?
   - Create `bots` table?
   - Migrate from in-memory to database?

2. **What's the priority?**
   - Quick fix: Restore bot manually
   - Long-term: Database persistence

3. **Bot recovery:**
   - Can we recover bot definition from Hummingbot?
   - Or need to recreate from scratch?

---

## 🔧 **Proposed Solution**

### **Phase 1: Database Schema**
```sql
CREATE TABLE bots (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    account_identifier VARCHAR NOT NULL,
    strategy VARCHAR NOT NULL,
    connector VARCHAR NOT NULL,
    pair VARCHAR NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR DEFAULT 'stopped',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bots_account ON bots(account_identifier);
CREATE INDEX idx_bots_status ON bots(status);
```

### **Phase 2: Update BotManager**
```python
class BotManager:
    def __init__(self, exchange_manager, db):
        self.exchange_manager = exchange_manager
        self.hummingbot_client = HummingbotClient()
        self.db = db  # Database connection
    
    async def create_bot(self, name, account, ...):
        # 1. Deploy to Hummingbot
        await self.hummingbot_client.deploy_script(...)
        
        # 2. Store in database
        await self.db.create_bot({
            "id": name,
            "name": name,
            "account_identifier": account,
            ...
        })
    
    async def list_bots(self, account=None):
        # 1. Get from database
        bots = await self.db.get_bots(account=account)
        
        # 2. Enrich with Hummingbot status
        hb_status = await self.hummingbot_client.get_status()
        # ... merge status ...
        
        return {"bots": bots}
```

---

## ✅ **Immediate Action**

**To restore the Sharp bot:**

1. **Check Hummingbot status:**
   ```bash
   curl -u admin:admin -H "ngrok-skip-browser-warning: true" \
     https://unpolymerized-singlemindedly-theda.ngrok-free.dev/bot-orchestration/status
   ```

2. **If bot exists in Hummingbot:**
   - We can add it back to metadata
   - Or recreate via UI (will sync to metadata)

3. **If bot doesn't exist:**
   - Need to recreate from scratch
   - Use same account identifier: `client_sharp`

---

**Please advise on:**
1. Should we implement database persistence?
2. How to recover the lost bot?
3. Priority: Quick fix vs. long-term solution?
