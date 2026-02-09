# Client Dashboard — Missing "Start Bot" Button

**Date:** 2026-02-05  
**Issue:** Client sees bot card with "Stopped" status but no "Start Bot" button

---

## 🔍 **What Client Sees**

**Bot Card Display:**
- ✅ Bot name: "Lynk"
- ✅ Bot type: "Volume Bot · jupiter (solana)"
- ✅ Status indicator: "Stopped" (red pill)
- ✅ "Edit Settings" button
- ❌ **Missing: "Start Bot" button**

**Expected Behavior:**
- When bot status = "stopped" → Show "Start Bot" button
- When bot status = "running" → Show "Stop Bot" button
- Always show "Edit Settings" button

---

## 📋 **Current Implementation**

According to `CLIENT_DASHBOARD_REDESIGN_COMPLETE.md`:
- ✅ Start/Stop/Edit buttons should be displayed
- ✅ Clients can start/stop their own bots
- ✅ Backend authorization checks are in place

**But the frontend is not rendering the Start/Stop button.**

---

## 🎯 **What Needs to Be Fixed**

### **Frontend (`ai-trading-ui/src/pages/ClientDashboard.jsx`)**

The bot card should conditionally render:

```jsx
{/* Bot Action Buttons */}
<div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
  {/* Start/Stop Button - Show based on bot status */}
  {bot.status === 'running' ? (
    <button 
      onClick={() => handleStopBot(bot.id)}
      style={{
        padding: '10px 20px',
        backgroundColor: '#ef4444',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer'
      }}
    >
      Stop Bot
    </button>
  ) : (
    <button 
      onClick={() => handleStartBot(bot.id)}
      style={{
        padding: '10px 20px',
        backgroundColor: '#10b981',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer'
      }}
    >
      Start Bot
    </button>
  )}
  
  {/* Edit Button - Always shown */}
  <button 
    onClick={() => handleEditBot(bot)}
    style={{
      padding: '10px 20px',
      backgroundColor: '#6366f1',
      color: 'white',
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer'
    }}
  >
    Edit Settings
  </button>
</div>
```

---

## 🔧 **Backend Endpoints (Already Working)**

- ✅ `POST /bots/{bot_id}/start` - Start bot (with authorization)
- ✅ `POST /bots/{bot_id}/stop` - Stop bot (with authorization)
- ✅ `PUT /bots/{bot_id}` - Update bot config (with authorization)

---

## 📝 **Action Items**

1. **Frontend Fix:**
   - Add conditional rendering for Start/Stop button based on `bot.status`
   - Ensure button calls correct API endpoint (`/bots/{bot_id}/start` or `/bots/{bot_id}/stop`)
   - Add loading state while request is processing
   - Refresh bot status after start/stop action

2. **Testing:**
   - Test with bot status = "stopped" → Should show "Start Bot"
   - Test with bot status = "running" → Should show "Stop Bot"
   - Test button click → Should call API and update status
   - Test error handling → Show error message if API call fails

---

## 🎨 **UI/UX Recommendations**

**Button Placement:**
- Place Start/Stop button next to "Edit Settings" button
- Use green color for "Start Bot" (#10b981)
- Use red color for "Stop Bot" (#ef4444)
- Use blue/purple color for "Edit Settings" (#6366f1)

**Button States:**
- Default: Full opacity, clickable
- Loading: Show spinner, disable button
- Success: Refresh bot card, update status
- Error: Show error message below button

---

## ✅ **Expected Result**

After fix, client should see:

**When Bot is Stopped:**
```
[Stopped] Status indicator
[Start Bot] [Edit Settings] Buttons
```

**When Bot is Running:**
```
[Running] Status indicator  
[Stop Bot] [Edit Settings] Buttons
```

---

**Status:** ⚠️ Frontend fix needed  
**Priority:** High (clients cannot start their bots)
