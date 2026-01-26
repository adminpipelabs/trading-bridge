# Bot Persistence Issue - Need Dev Advice

**Date:** 2026-01-26  
**Priority:** High - Bots disappearing after service restart

---

## 🔴 **Current Problem**

**Issue:** Bot created for "Sharp" client (`account: "client_sharp"`) is no longer visible after Railway redeploy.

**Symptoms:**
- `/bots` endpoint returns `{"bots": []}` (empty)
- Bot not visible in Bot Management UI
- Client can't see bot configuration
- No Running/Stopped status, no Edit button

**Root Cause:**
```python
# app/bot_routes.py
class BotManager:
    def __init__(self, exchange_manager):
        self.bot_metadata = {}  # ❌ In-memory storage - lost on restart
```

**What happens:**
1. Admin creates bot → stored in `self.bot_metadata` (memory)
2. Railway redeploys → service restarts
3. `bot_metadata` is empty → bot disappears
4. Only bots currently running in Hummingbot would be visible (via `/status`)

---

## ❓ **Questions for Dev**

### **1. Database Persistence - Should we implement?**

**Current:** In-memory storage (`self.bot_metadata = {}`)

**Proposed:** Store bot definitions in PostgreSQL

**Schema:**
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
```

**Benefits:**
- ✅ Persists across restarts
- ✅ Can query by account
- ✅ Full bot history
- ✅ Production-ready

**Questions:**
- Should we implement this now?
- Use existing PostgreSQL connection?
- Or keep in-memory for now and handle restarts differently?

---

### **2. Bot Recovery - How to restore lost bot?**

**Current situation:**
- Bot was created with `account: "client_sharp"`
- Bot metadata lost after restart
- Need to restore or recreate

**Options:**

**Option A: Check Hummingbot**
- Bot might still exist in Hummingbot (if it was running)
- Can we recover bot definition from Hummingbot API?
- Endpoint: `/bot-orchestration/status` or `/bot-orchestration/bot-runs`

**Option B: Recreate manually**
- Admin recreates bot via UI
- Uses same `account: "client_sharp"`
- Bot appears again

**Option C: Database migration**
- If we implement database persistence
- Migrate existing bots from Hummingbot to database
- One-time sync script

**Question:** Which approach do you prefer?

---

### **3. Architecture Decision**

**Current architecture (from your earlier guidance):**
> "Trading Bridge should be the source of truth for bot definitions, with Hummingbot providing runtime status."

**Current implementation:**
- ✅ Trading Bridge stores bot definitions (`bot_metadata`)
- ✅ Hummingbot provides runtime status (`/status`)
- ❌ But `bot_metadata` is in-memory (not persistent)

**Proposed architecture:**
```
┌─────────────────────────────────────────┐
│         Trading Bridge                   │
│                                         │
│  ┌──────────────────┐                  │
│  │  PostgreSQL      │                  │
│  │  (bot definitions)│                  │
│  │  - Source of truth│                  │
│  └──────────────────┘                  │
│            │                            │
│            ▼                            │
│  ┌──────────────────┐                  │
│  │  Hummingbot API   │                  │
│  │  (runtime status) │                  │
│  └──────────────────┘                  │
│                                         │
│  Merge: Definitions + Runtime Status    │
└─────────────────────────────────────────┘
```

**Question:** Does this align with your vision? Should we proceed with database persistence?

---

## 🛠️ **What I Can Do**

### **Option 1: Quick Fix (Temporary)**
- Check if bot exists in Hummingbot
- If yes: Add back to `bot_metadata` manually
- If no: Admin recreates via UI
- **Issue:** Will be lost again on next restart

### **Option 2: Database Persistence (Long-term)**
- Create `bots` table in PostgreSQL
- Update `BotManager` to use database
- Migrate existing bots (if any)
- **Benefit:** Permanent solution

### **Option 3: Hybrid Approach**
- Keep in-memory for now
- Add recovery mechanism:
  - On startup, query Hummingbot for running bots
  - Rebuild `bot_metadata` from Hummingbot
  - **Limitation:** Only recovers running bots, not stopped ones

---

## 📋 **Recommendation**

**For production:** Implement database persistence (Option 2)

**Reasons:**
1. Matches your architecture guidance (Trading Bridge = source of truth)
2. Prevents data loss on restart
3. Enables querying by account identifier
4. Production-ready solution

**Quick win:** Implement Option 1 to restore bot immediately, then Option 2 for long-term.

---

## ✅ **What I Need**

**Please advise:**
1. **Database persistence:** Should we implement now? (Yes/No)
2. **Bot recovery:** How to restore the lost bot? (Check Hummingbot / Recreate / Wait for DB)
3. **Priority:** Quick fix first, or go straight to database?

**Once I have your guidance, I'll:**
- Implement the solution
- Test end-to-end
- Document the changes

---

**Ready to implement once I have your direction!** 🚀
