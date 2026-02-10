# Frontend Fix: Add Start/Stop Bot Buttons to Client Dashboard

**Date:** 2026-02-05  
**Priority:** High  
**Issue:** Client Dashboard bot card missing Start/Stop buttons

---

## 🔍 **Problem**

**Current State:**
- Client sees bot card with "Stopped" status
- "Edit Settings" button is visible ✅
- **"Start Bot" button is missing** ❌

**Expected State:**
- When bot is stopped → Show "Start Bot" button
- When bot is running → Show "Stop Bot" button
- Always show "Edit Settings" button

---

## 📋 **What Needs to Be Fixed**

### **File:** `ai-trading-ui/src/pages/ClientDashboard.jsx`

The bot card needs to conditionally render Start/Stop buttons based on `bot.status`.

---

## 🎯 **Implementation Guide**

### **1. Add Handler Functions**

Add these functions to handle bot start/stop actions:

```jsx
// In ClientDashboard.jsx component

const handleStartBot = async (botId) => {
  try {
    setLoading(true);
    const response = await tradingBridge.startBot(botId);
    if (response.status === 'started' || response.status === 'already_running') {
      // Refresh bot list to update status
      await fetchBots();
      // Show success message (optional)
      console.log('Bot started successfully');
    }
  } catch (error) {
    console.error('Failed to start bot:', error);
    // Show error message to user
    alert(`Failed to start bot: ${error.message || 'Unknown error'}`);
  } finally {
    setLoading(false);
  }
};

const handleStopBot = async (botId) => {
  try {
    setLoading(true);
    const response = await tradingBridge.stopBot(botId);
    if (response.status === 'stopped' || response.status === 'already_stopped') {
      // Refresh bot list to update status
      await fetchBots();
      // Show success message (optional)
      console.log('Bot stopped successfully');
    }
  } catch (error) {
    console.error('Failed to stop bot:', error);
    // Show error message to user
    alert(`Failed to stop bot: ${error.message || 'Unknown error'}`);
  } finally {
    setLoading(false);
  }
};
```

### **2. Update Bot Card Rendering**

Find where the bot card is rendered (likely in the Dashboard tab section) and add the Start/Stop buttons:

```jsx
// In the bot card rendering section

{clientBots.map((bot) => (
  <div key={bot.id} style={{
    padding: '20px',
    borderRadius: '8px',
    backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
    border: `1px solid ${theme === 'dark' ? '#374151' : '#e5e7eb'}`,
    marginBottom: '16px'
  }}>
    {/* Bot Header */}
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
      <div>
        <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>{bot.name}</h3>
        <p style={{ margin: '4px 0 0 0', color: '#6b7280', fontSize: '14px' }}>
          {bot.bot_type === 'volume' ? 'Volume Bot' : 'Spread Bot'} · {bot.connector || 'Unknown'}
        </p>
      </div>
      {/* Status Badge */}
      <div style={{
        padding: '6px 12px',
        borderRadius: '20px',
        backgroundColor: bot.status === 'running' ? '#10b981' : '#ef4444',
        color: 'white',
        fontSize: '12px',
        fontWeight: '600'
      }}>
        {bot.status === 'running' ? 'Running' : 'Stopped'}
      </div>
    </div>

    {/* Bot Stats - Your existing stats display */}
    {/* ... existing stats code ... */}

    {/* Action Buttons */}
    <div style={{ 
      display: 'flex', 
      flexDirection: window.innerWidth < 768 ? 'column' : 'row', // Stack on mobile
      gap: '12px', 
      marginTop: '20px',
      paddingTop: '16px',
      borderTop: `1px solid ${theme === 'dark' ? '#374151' : '#e5e7eb'}`
    }}>
      {/* Start/Stop Button - Conditional based on bot status */}
      {bot.status === 'running' ? (
        <button
          onClick={() => handleStopBot(bot.id)}
          disabled={loading}
          style={{
            padding: '12px 20px', // Increased padding for mobile touch targets
            minHeight: '44px', // iOS/Android minimum touch target
            backgroundColor: '#ef4444',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            opacity: loading ? 0.6 : 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            width: window.innerWidth < 768 ? '100%' : 'auto', // Full width on mobile
            transition: 'opacity 0.2s, transform 0.1s',
            WebkitTapHighlightColor: 'transparent' // Remove mobile tap highlight
          }}
          onTouchStart={(e) => {
            if (!loading) e.currentTarget.style.opacity = '0.8';
          }}
          onTouchEnd={(e) => {
            e.currentTarget.style.opacity = '1';
          }}
        >
          {loading ? (
            <>
              <span className="spinner" /> Stopping...
            </>
          ) : (
            <>
              <span>⏹</span> Stop Bot
            </>
          )}
        </button>
      ) : (
        <button
          onClick={() => handleStartBot(bot.id)}
          disabled={loading}
          style={{
            padding: '12px 20px', // Increased padding for mobile touch targets
            minHeight: '44px', // iOS/Android minimum touch target
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            opacity: loading ? 0.6 : 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            width: window.innerWidth < 768 ? '100%' : 'auto', // Full width on mobile
            transition: 'opacity 0.2s, transform 0.1s',
            WebkitTapHighlightColor: 'transparent' // Remove mobile tap highlight
          }}
          onTouchStart={(e) => {
            if (!loading) e.currentTarget.style.opacity = '0.8';
          }}
          onTouchEnd={(e) => {
            e.currentTarget.style.opacity = '1';
          }}
        >
          {loading ? (
            <>
              <span className="spinner" /> Starting...
            </>
          ) : (
            <>
              <span>▶</span> Start Bot
            </>
          )}
        </button>
      )}

      {/* Edit Button - Always visible */}
      <button
        onClick={() => handleEditBot(bot)}
        style={{
          padding: '12px 20px', // Increased padding for mobile touch targets
          minHeight: '44px', // iOS/Android minimum touch target
          backgroundColor: '#6366f1',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: '500',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          width: window.innerWidth < 768 ? '100%' : 'auto', // Full width on mobile
          transition: 'opacity 0.2s',
          WebkitTapHighlightColor: 'transparent' // Remove mobile tap highlight
        }}
        onTouchStart={(e) => {
          e.currentTarget.style.opacity = '0.8';
        }}
        onTouchEnd={(e) => {
          e.currentTarget.style.opacity = '1';
        }}
      >
        <span>✏️</span> Edit Settings
      </button>
    </div>
  </div>
))}
```

### **3. Verify API Functions Exist**

Check `ai-trading-ui/src/services/api.js` to ensure these functions exist:

```javascript
// In api.js - should already exist, but verify:

startBot: async (botId) => {
  return apiCall(`${TRADING_BRIDGE_URL}/bots/${botId}/start`, {
    method: 'POST',
    headers: {
      'X-Wallet-Address': getWalletAddress(), // Get from auth context
    },
  });
},

stopBot: async (botId) => {
  return apiCall(`${TRADING_BRIDGE_URL}/bots/${botId}/stop`, {
    method: 'POST',
    headers: {
      'X-Wallet-Address': getWalletAddress(), // Get from auth context
    },
  });
},
```

If they don't exist, add them!

### **4. Add Loading State**

Add a loading state to prevent multiple clicks:

```jsx
const [loading, setLoading] = useState(false);
```

---

## 🎨 **Button Styling**

**Start Bot Button:**
- Background: `#10b981` (green)
- Text: White
- Icon: ▶ (play symbol)

**Stop Bot Button:**
- Background: `#ef4444` (red)
- Text: White
- Icon: ⏹ (stop symbol)

**Edit Settings Button:**
- Background: `#6366f1` (indigo/purple)
- Text: White
- Icon: ✏️ (pencil)

**Button States:**
- Default: Full opacity, clickable
- Loading: 60% opacity, disabled, show spinner
- Hover: Slightly darker shade (desktop only)

**Mobile-Specific Requirements:**
- Minimum touch target: 44x44px (iOS/Android guidelines)
- Adequate spacing between buttons (12-16px gap)
- Full-width buttons on mobile (< 768px) for easier tapping
- Stack buttons vertically on mobile if needed
- Clear visual feedback on tap (slight scale or color change)

---

## 🧪 **Testing Checklist**

After implementation, test:

1. **Bot Status = "stopped":**
   - ✅ "Start Bot" button is visible
   - ✅ "Edit Settings" button is visible
   - ✅ Click "Start Bot" → API call succeeds → Status updates to "running"
   - ✅ Button changes to "Stop Bot"

2. **Bot Status = "running":**
   - ✅ "Stop Bot" button is visible
   - ✅ "Edit Settings" button is visible
   - ✅ Click "Stop Bot" → API call succeeds → Status updates to "stopped"
   - ✅ Button changes to "Start Bot"

3. **Error Handling:**
   - ✅ If API call fails → Show error message
   - ✅ Button returns to original state
   - ✅ User can retry

4. **Loading States:**
   - ✅ Button shows loading spinner while request is processing
   - ✅ Button is disabled during loading
   - ✅ Multiple clicks are prevented

5. **Status Updates:**
   - ✅ After start/stop → Bot card refreshes
   - ✅ Status badge updates correctly
   - ✅ Button text changes correctly

6. **Mobile Testing:**
   - ✅ Buttons are touch-friendly (44px minimum height)
   - ✅ Buttons stack vertically on mobile screens
   - ✅ Full-width buttons on mobile for easier tapping
   - ✅ Visual feedback on tap (opacity change)
   - ✅ No accidental double-taps
   - ✅ Loading states are clear on mobile

---

## 📡 **Backend Endpoints (Already Working)**

The backend endpoints are already implemented and working:

- ✅ `POST /bots/{bot_id}/start` - Start bot (with authorization check)
- ✅ `POST /bots/{bot_id}/stop` - Stop bot (with authorization check)
- ✅ `PUT /bots/{bot_id}` - Update bot config (with authorization check)

**Response Format:**
```json
{
  "status": "started" | "stopped" | "already_running" | "already_stopped",
  "bot_id": "uuid-string"
}
```

---

## 🔒 **Authorization**

Backend already checks authorization:
- ✅ Clients can only start/stop their own bots
- ✅ Admin can start/stop any bot
- ✅ Unauthorized requests return 403

Frontend doesn't need to check authorization - backend handles it.

---

## 📝 **Summary**

**What to Change:**
1. Add `handleStartBot` and `handleStopBot` functions
2. Add conditional rendering for Start/Stop button based on `bot.status`
3. Ensure "Edit Settings" button is always visible
4. Add loading state to prevent multiple clicks
5. Refresh bot list after start/stop action

**Files to Modify:**
- `ai-trading-ui/src/pages/ClientDashboard.jsx` - Add handlers and button rendering
- `ai-trading-ui/src/services/api.js` - Verify `startBot` and `stopBot` functions exist

**Expected Result:**
- When bot is stopped → Show "Start Bot" + "Edit Settings"
- When bot is running → Show "Stop Bot" + "Edit Settings"
- Buttons work correctly and update status

---

**Status:** ⚠️ Frontend implementation needed  
**Backend:** ✅ Ready  
**Priority:** High
