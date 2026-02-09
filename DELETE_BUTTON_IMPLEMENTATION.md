# Delete Bot Button - Implementation Guide

## ✅ Backend Fixed

**File:** `app/bot_routes.py`

**Changes:**
- ✅ Added authorization check to `DELETE /bots/{bot_id}` endpoint
- ✅ Clients can delete their own bots
- ✅ Admins can delete any bot
- ✅ Bot is stopped before deletion

---

## 🎨 Frontend Implementation

### 1. Add Delete Button to Bot Card

**File:** `ai-trading-ui/src/pages/ClientDashboard.jsx`

**Add this to the bot card actions:**

```jsx
// Add state for delete confirmation
const [deleteConfirmBot, setDeleteConfirmBot] = useState(null);

// Add delete handler
const handleDeleteBot = async (botId, botName) => {
  try {
    setLoading(true);
    const response = await fetch(`${API_BASE}/bots/${botId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-Wallet-Address': walletAddress, // Or your auth header
        // ... other headers
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete bot');
    }
    
    // Refresh bot list
    await fetchBots();
    setDeleteConfirmBot(null);
    alert(`Bot "${botName}" deleted successfully`);
  } catch (error) {
    console.error('Failed to delete bot:', error);
    alert(`Failed to delete bot: ${error.message}`);
  } finally {
    setLoading(false);
  }
};

// Add delete button in bot card
<div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
  {/* Start/Stop Button */}
  {bot.status === 'running' ? (
    <button onClick={() => handleStopBot(bot.id)}>
      ⏹️ Stop Bot
    </button>
  ) : (
    <button onClick={() => handleStartBot(bot.id)}>
      ▶️ Start Bot
    </button>
  )}
  
  {/* Edit Button */}
  <button onClick={() => handleEdit(bot)}>
      ✏️ Edit
  </button>
  
  {/* ✅ DELETE BUTTON */}
  <button
    onClick={() => setDeleteConfirmBot(bot)}
    style={{
      padding: '8px 16px',
      backgroundColor: 'transparent',
      color: '#EF4444',
      border: '1px solid #EF4444',
      borderRadius: '8px',
      fontWeight: 600,
      fontSize: '14px',
      cursor: 'pointer'
    }}
  >
    🗑️ Delete
  </button>
</div>
```

---

### 2. Add Confirmation Modal

**Add this modal component:**

```jsx
{/* Delete Confirmation Modal */}
{deleteConfirmBot && (
  <div style={{
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000
  }}
  onClick={() => setDeleteConfirmBot(null)}
  >
    <div 
      style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '12px',
        maxWidth: '400px',
        width: '90%',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <h3 style={{ marginBottom: '16px', fontSize: '20px', fontWeight: 700 }}>
        Delete Bot?
      </h3>
      <p style={{ color: '#6B7280', marginBottom: '24px', lineHeight: '1.5' }}>
        Are you sure you want to delete <strong>"{deleteConfirmBot.name}"</strong>?
        <br /><br />
        This action cannot be undone. The bot will be stopped and all configuration will be lost.
      </p>
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
        <button
          onClick={() => setDeleteConfirmBot(null)}
          style={{
            padding: '10px 20px',
            backgroundColor: '#F3F4F6',
            color: '#374151',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          Cancel
        </button>
        <button
          onClick={() => handleDeleteBot(deleteConfirmBot.id, deleteConfirmBot.name)}
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: '#EF4444',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? 'Deleting...' : 'Delete Bot'}
        </button>
      </div>
    </div>
  </div>
)}
```

---

## 📋 Complete Example

**Full bot card with delete button:**

```jsx
<div className="bot-card" style={{ /* ... card styles ... */ }}>
  {/* Bot Header */}
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <div>
      <h3>{bot.name}</h3>
      <StatusBadge status={bot.status} />
    </div>
  </div>
  
  {/* Error/Warning Messages */}
  {bot.health_message && (
    <div style={{ /* ... warning styles ... */ }}>
      {bot.health_message}
    </div>
  )}
  
  {/* Balance Display */}
  <div>
    {/* ... balance display ... */}
  </div>
  
  {/* Action Buttons */}
  <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
    {/* Start/Stop */}
    {bot.status === 'running' ? (
      <button onClick={() => handleStopBot(bot.id)}>⏹️ Stop</button>
    ) : (
      <button onClick={() => handleStartBot(bot.id)}>▶️ Start</button>
    )}
    
    {/* Edit */}
    <button onClick={() => handleEdit(bot)}>✏️ Edit</button>
    
    {/* ✅ DELETE */}
    <button
      onClick={() => setDeleteConfirmBot(bot)}
      style={{
        padding: '8px 16px',
        backgroundColor: 'transparent',
        color: '#EF4444',
        border: '1px solid #EF4444',
        borderRadius: '8px',
        fontWeight: 600,
        cursor: 'pointer'
      }}
    >
      🗑️ Delete
    </button>
  </div>
</div>

{/* Delete Confirmation Modal */}
{deleteConfirmBot && (
  <div style={{ /* ... modal styles ... */ }}>
    {/* ... modal content ... */}
  </div>
)}
```

---

## ✅ Testing Checklist

1. ✅ **Delete button appears** on bot cards
2. ✅ **Click delete** → Confirmation modal appears
3. ✅ **Click Cancel** → Modal closes, bot not deleted
4. ✅ **Click Delete Bot** → Bot is deleted, list refreshes
5. ✅ **Try to delete other client's bot** → Should fail (403)
6. ✅ **Delete running bot** → Bot stops first, then deletes

---

## 🎯 Summary

**Backend:** ✅ Fixed - Added authorization check
**Frontend:** ⏳ Needs implementation - Add delete button + confirmation modal

**Time:** ~15 minutes to implement

**Result:** Clients can delete unwanted bots safely with confirmation.
