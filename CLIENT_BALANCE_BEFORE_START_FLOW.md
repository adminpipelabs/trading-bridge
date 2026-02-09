# Client Balance Display Before Bot Activation

## ✅ **Flow: Client Sees Balance → Then Activates Bot**

### **Backend Endpoint: `GET /api/bots/{bot_id}/stats`**

**Works for:** Both stopped and running bots (fetches live balance from exchange)

**Response Format:**
```json
{
  "available": {
    "SHARP": 8364285.05,
    "USDT": 1.66
  },
  "locked": {
    "SHARP": 0,
    "USDT": 0
  },
  "volume_24h": 0,
  "trades_24h": {
    "buys": 0,
    "sells": 0
  },
  "balance_error": null  // Only present if balance fetch failed
}
```

**Error Handling:**
- If balance fetch fails, `balance_error` field contains user-friendly message:
  - `"IP whitelist required - add Railway IPs to exchange API settings"`
  - `"API authentication failed - check API keys and permissions"`
  - `"Exchange connector not found - check API keys are configured"`

---

## 🎨 **Frontend Implementation**

### **1. Bot Card Display (Stopped Bot)**

**When bot status = "stopped":**

```jsx
// Fetch balance on component mount
useEffect(() => {
  const fetchBalance = async () => {
    try {
      const response = await fetch(`/api/bots/${bot.id}/stats`);
      const data = await response.json();
      setBalance(data);
    } catch (error) {
      setBalanceError("Failed to load balance");
    }
  };
  
  if (bot.status === 'stopped') {
    fetchBalance(); // Show balance even when stopped
  }
}, [bot.id, bot.status]);

// Display in bot card
<div className="bot-balance">
  {balance ? (
    <>
      <div>Available: {balance.available.SHARP} SHARP | {balance.available.USDT} USDT</div>
      <div>Locked: {balance.locked.SHARP} SHARP | {balance.locked.USDT} USDT</div>
      {balance.balance_error && (
        <div className="error">{balance.balance_error}</div>
      )}
    </>
  ) : (
    <div>Loading balance...</div>
  )}
</div>

// Start button (only enabled if balance loaded)
<button 
  onClick={handleStart}
  disabled={!balance || balance.balance_error}
>
  Start Bot
</button>
```

### **2. Display Format**

**For Volume Bots:**
```
Available: 8,364,285.05 SHARP | 1.66 USDT
Locked: 0 SHARP | 0 USDT
Volume: $0 (24h)
```

**For Spread Bots:**
```
Available: 8,364,285.05 SHARP | 1.66 USDT
Locked: 0 SHARP | 0 USDT
Trades: 0 buys, 0 sells (24h)
```

### **3. Error States**

**If `balance_error` is present:**
- Show error message in red/yellow warning box
- Disable "Start Bot" button
- Show "Fix API Keys" link/button

**Example:**
```jsx
{balance?.balance_error && (
  <div style={{
    padding: '12px',
    backgroundColor: '#fffbeb',
    border: '1px solid #fbbf24',
    borderRadius: '6px',
    marginBottom: '12px'
  }}>
    ⚠️ {balance.balance_error}
    <button onClick={() => navigate('/settings/api-keys')}>
      Fix API Keys
    </button>
  </div>
)}
```

---

## 🔄 **User Flow**

1. **Client creates bot** → Bot status = "stopped"
2. **Bot card displays** → Automatically fetches balance via `/bots/{id}/stats`
3. **Balance shows** → Client sees Available/Locked funds
4. **If balance OK** → "Start Bot" button enabled
5. **If balance error** → Error message shown, "Start Bot" disabled
6. **Client clicks "Start Bot"** → Bot status changes to "running"
7. **Balance continues updating** → Same endpoint works for running bots too

---

## 📋 **Key Points**

✅ **Balance fetches work for stopped bots** - No need to start bot first
✅ **Clear error messages** - Frontend can display helpful messages
✅ **Same endpoint for all states** - Works for stopped, running, error states
✅ **Real-time balance** - Fetches directly from exchange API
✅ **No bot status dependency** - Balance fetch doesn't require bot to be running

---

## 🚀 **Next Steps for Frontend**

1. **Update bot card component** to call `/bots/{id}/stats` on mount
2. **Display balance** in format: `Available: X SHARP | Y USDT`
3. **Show error messages** if `balance_error` field is present
4. **Disable Start button** if balance fetch fails
5. **Add "Refresh Balance" button** for manual refresh

---

## 🔧 **Backend Status**

✅ Endpoint implemented: `/api/bots/{bot_id}/stats`
✅ Error handling improved
✅ Works for stopped bots
✅ Returns clear error messages
✅ Ready for frontend integration
