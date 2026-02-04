# Client Bot Permissions — Explanation for Dev

## 🔍 **What You're Seeing**

You logged in as **client "Lynk"** and see:
- ✅ **ClientDashboard** (correct — routing works!)
- ✅ Bot list showing your bot "Lynk"
- ⚠️ **Stop, Edit, Delete buttons** visible on your bot

---

## 📋 **Current Implementation**

### **ClientDashboard.jsx** (line 383)
```javascript
<BotList 
  bots={clientBots} 
  account={client.account_identifier}
  readOnly={false}  // ← This allows Stop/Edit/Delete buttons
/>
```

### **BotList.jsx** (lines 166-225)
The component shows Stop/Edit/Delete buttons when `readOnly={false}`:
- **Stop/Start button** - Toggles bot status
- **Edit button** - Opens edit modal
- **Delete button** - Deletes bot (with confirmation)

---

## ❓ **Question: What Should Clients Be Able to Do?**

Based on the codebase, I found **no explicit instructions** about client permissions. Here's what I found:

### **What Was Implemented:**
1. ✅ **Client Self-Service Bot Setup** (`CLIENT_SELF_SERVICE_DEPLOYMENT.md`)
   - Clients can create bots via `POST /clients/{id}/setup-bot`
   - Clients can rotate keys via `PUT /clients/{id}/rotate-key`
   - Clients can revoke keys via `DELETE /clients/{id}/revoke-key`

2. ✅ **Frontend UI** (`FRONTEND_UI_STATUS.md`)
   - Mentions "User can start/stop bots" (line 74)
   - No mention of Edit/Delete permissions

### **What's Missing:**
- ❌ No explicit instructions about client bot management permissions
- ❌ No backend authorization checks for client bot operations
- ❌ No distinction between "client-created bots" vs "admin-created bots"

---

## 🎯 **Recommended Permissions**

### **Option A: Full Self-Service (Current Implementation)**
Clients can:
- ✅ **Start/Stop** their own bots
- ✅ **Edit** their own bots (config changes)
- ✅ **Delete** their own bots

**Rationale:** If clients created the bot themselves, they should manage it.

### **Option B: Limited Self-Service**
Clients can:
- ✅ **Start/Stop** their own bots
- ❌ **Edit** bots (admin only)
- ❌ **Delete** bots (admin only)

**Rationale:** Prevent clients from breaking bot configs.

### **Option C: View Only**
Clients can:
- ❌ **Start/Stop** bots (admin only)
- ❌ **Edit** bots (admin only)
- ❌ **Delete** bots (admin only)

**Rationale:** Clients only view status, admin manages everything.

---

## 🔒 **Security Concerns**

### **Current Backend Status:**
Looking at `app/bot_routes.py`:
- ✅ `POST /bots/{id}/start` - No authorization check (anyone can start any bot)
- ✅ `POST /bots/{id}/stop` - No authorization check (anyone can stop any bot)
- ✅ `PUT /bots/{id}` - No authorization check (anyone can edit any bot)
- ✅ `DELETE /bots/{id}` - No authorization check (anyone can delete any bot)

**⚠️ CRITICAL:** Backend has **NO authorization checks**. Any authenticated user can:
- Start/stop ANY bot
- Edit ANY bot
- Delete ANY bot

---

## 📝 **What Needs to Be Decided**

1. **Should clients be able to start/stop their own bots?**
   - If YES: Backend needs authorization check (only allow if `bot.client_id === current_user.client_id`)
   - If NO: Hide Start/Stop buttons for clients

2. **Should clients be able to edit their own bots?**
   - If YES: Backend needs authorization check
   - If NO: Set `readOnly={true}` in ClientDashboard

3. **Should clients be able to delete their own bots?**
   - If YES: Backend needs authorization check
   - If NO: Hide Delete button for clients

4. **Should clients see admin-created bots?**
   - Current: Clients see ALL bots for their account
   - Question: Should they only see bots they created?

---

## 🛠️ **Quick Fix Options**

### **Option 1: Make Client Dashboard Read-Only**
Change `ClientDashboard.jsx` line 383:
```javascript
<BotList 
  bots={clientBots} 
  account={client.account_identifier}
  readOnly={true}  // ← Hide Stop/Edit/Delete buttons
/>
```

### **Option 2: Add Backend Authorization**
Add checks in `app/bot_routes.py`:
```python
@router.post("/{bot_id}/start")
async def start_bot(bot_id: str, db: Session = Depends(get_db), current_user: Client = Depends(get_current_client)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Authorization check
    if current_user.role != 'admin' and bot.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to start this bot")
    
    # ... rest of code
```

---

## 🎯 **Recommendation**

**For now:** Set `readOnly={true}` in ClientDashboard until we clarify:
1. What permissions clients should have
2. Whether backend authorization is needed
3. How to distinguish client-created vs admin-created bots

**Then:** Implement proper authorization checks in backend.

---

## 📋 **Files to Check**

1. **Frontend:**
   - `ai-trading-ui/src/pages/ClientDashboard.jsx` (line 383)
   - `ai-trading-ui/src/components/BotList.jsx` (lines 166-225)

2. **Backend:**
   - `app/bot_routes.py` (lines 501-822)
   - No authorization checks currently

3. **Design Docs:**
   - `CLIENT_SELF_SERVICE_DEPLOYMENT.md` - Mentions setup but not management
   - `FRONTEND_UI_STATUS.md` - Mentions "start/stop" but not permissions

---

## ❓ **Questions for Dev**

1. **Should clients be able to start/stop their own bots?**
2. **Should clients be able to edit their own bots?**
3. **Should clients be able to delete their own bots?**
4. **Should clients see admin-created bots or only their own?**
5. **Do we need backend authorization checks, or is frontend hiding enough?**

Once we have answers, I can implement the proper permissions!
