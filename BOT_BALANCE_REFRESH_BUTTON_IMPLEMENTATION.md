# Bot Balance Refresh Button - Implementation Guide

## 🎯 Goal
Add a refresh button (↻) to each bot card that manually refreshes that bot's balance without reloading the entire page.

---

## 📍 Where to Add It

Based on the bot card UI you showed:
- **Location**: Next to the balance display (Available/Locked section)
- **Style**: Small icon button, similar to Edit/Delete buttons
- **Behavior**: Click → Fetch fresh balance → Update display

---

## 🔧 Implementation

### Step 1: Add Refresh Handler to Bot Card Component

```jsx
const BotCard = ({ bot, walletAddress, account, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [balanceLoading, setBalanceLoading] = useState(false);
  const [balance, setBalance] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const isRunning = bot.status === 'running';
  
  // Fetch balance on mount
  useEffect(() => {
    const fetchBalance = async () => {
      setBalanceLoading(true);
      try {
        const response = await fetch(`/api/bots/${bot.id}/stats`);
        const data = await response.json();
        setBalance(data);
      } catch (error) {
        console.error('Failed to load balance:', error);
      } finally {
        setBalanceLoading(false);
      }
    };
    
    fetchBalance();
  }, [bot.id]);

  // ✅ NEW: Refresh balance handler
  const handleRefreshBalance = async () => {
    setBalanceLoading(true);
    try {
      const response = await fetch(`/api/bots/${bot.id}/stats`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setBalance(data);
      
      // Also update parent component if needed
      if (onUpdate) {
        onUpdate();
      }
    } catch (error) {
      console.error('Failed to refresh balance:', error);
      alert('Failed to refresh balance. Please try again.');
    } finally {
      setBalanceLoading(false);
    }
  };

  // Get balance data (use state if available, otherwise fallback to bot prop)
  const available = balance?.available || bot.available || bot.balance?.available || {};
  const locked = balance?.locked || bot.locked || bot.balance?.locked || {};
  const volume = balance?.volume_24h || bot.volume?.value_usd || bot.balance?.volume_24h || 0;
  const pnl = balance?.pnl?.total_usd || bot.pnl?.total_usd || 0;

  return (
    <div style={{
      backgroundColor: '#FFFFFF',
      border: '1px solid #E5E7EB',
      borderRadius: '12px',
      padding: '20px',
      marginBottom: '16px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
    }}>
      {/* Bot Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>
            {bot.name}
          </h3>
          <div style={{
            display: 'inline-block',
            padding: '4px 8px',
            borderRadius: '4px',
            backgroundColor: isRunning ? '#D1FAE5' : '#FEE2E2',
            color: isRunning ? '#065F46' : '#991B1B',
            fontSize: '12px',
            fontWeight: 500,
            marginTop: '4px'
          }}>
            {bot.status || 'Stopped'}
          </div>
        </div>
      </div>

      {/* Balance Section with Refresh Button */}
      <div style={{
        backgroundColor: '#F9FAFB',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '16px'
      }}>
        {/* Balance Header with Refresh Button */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px'
        }}>
          <h4 style={{
            margin: 0,
            fontSize: '14px',
            fontWeight: 600,
            color: '#374151'
          }}>
            Balance
          </h4>
          {/* ✅ REFRESH BUTTON */}
          <button
            onClick={handleRefreshBalance}
            disabled={balanceLoading}
            title="Refresh Balance"
            style={{
              padding: '6px 8px',
              backgroundColor: balanceLoading ? '#D1D5DB' : '#3B82F6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: balanceLoading ? 'wait' : 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'all 0.2s',
              opacity: balanceLoading ? 0.6 : 1
            }}
            onMouseEnter={(e) => {
              if (!balanceLoading) {
                e.currentTarget.style.backgroundColor = '#2563EB';
              }
            }}
            onMouseLeave={(e) => {
              if (!balanceLoading) {
                e.currentTarget.style.backgroundColor = '#3B82F6';
              }
            }}
          >
            <span style={{
              display: 'inline-block',
              animation: balanceLoading ? 'spin 1s linear infinite' : 'none'
            }}>
              {balanceLoading ? '⟳' : '↻'}
            </span>
            {balanceLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Available Funds */}
        <div style={{ marginBottom: '12px' }}>
          <div style={{
            fontSize: '12px',
            color: '#6B7280',
            fontWeight: 500,
            marginBottom: '4px'
          }}>
            Available
          </div>
          {balanceLoading && !balance ? (
            <div style={{ color: '#9CA3AF', fontSize: '14px' }}>Loading...</div>
          ) : (
            <div style={{
              fontSize: '14px',
              fontWeight: 600,
              color: '#111827'
            }}>
              {Object.keys(available).length > 0 ? (
                Object.entries(available)
                  .filter(([_, amount]) => amount > 0)
                  .map(([asset, amount]) => (
                    <span key={asset} style={{ marginRight: '12px' }}>
                      {amount.toLocaleString()} {asset}
                    </span>
                  ))
              ) : (
                <span style={{ color: '#9CA3AF' }}>0 SHARP | 0 USDT</span>
              )}
            </div>
          )}
        </div>

        {/* Locked Funds */}
        <div>
          <div style={{
            fontSize: '12px',
            color: '#6B7280',
            fontWeight: 500,
            marginBottom: '4px'
          }}>
            Locked
          </div>
          {balanceLoading && !balance ? (
            <div style={{ color: '#9CA3AF', fontSize: '14px' }}>Loading...</div>
          ) : (
            <div style={{
              fontSize: '14px',
              fontWeight: 600,
              color: '#111827'
            }}>
              {Object.keys(locked).length > 0 && Object.values(locked).some(v => v > 0) ? (
                Object.entries(locked)
                  .filter(([_, amount]) => amount > 0)
                  .map(([asset, amount]) => (
                    <span key={asset} style={{ marginRight: '12px' }}>
                      {amount.toLocaleString()} {asset}
                    </span>
                  ))
              ) : (
                <span style={{ color: '#9CA3AF' }}>0 SHARP | 0 USDT</span>
              )}
            </div>
          )}
        </div>

        {/* Error Message */}
        {balance?.balance_error && (
          <div style={{
            marginTop: '12px',
            padding: '8px 12px',
            backgroundColor: '#FEE2E2',
            border: '1px solid #FCA5A5',
            borderRadius: '6px',
            color: '#991B1B',
            fontSize: '12px'
          }}>
            ⚠️ {balance.balance_error}
          </div>
        )}
      </div>

      {/* Volume & P&L */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        marginBottom: '16px'
      }}>
        <div style={{
          backgroundColor: '#F0FDF4',
          padding: '12px',
          borderRadius: '8px',
          border: '1px solid #86EFAC'
        }}>
          <div style={{
            fontSize: '12px',
            color: '#6B7280',
            fontWeight: 500,
            marginBottom: '4px'
          }}>
            Volume
          </div>
          <div style={{
            fontSize: '18px',
            fontWeight: 700,
            color: '#059669'
          }}>
            ${volume.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>

        <div style={{
          backgroundColor: '#F0F9FF',
          padding: '12px',
          borderRadius: '8px',
          border: '1px solid #93C5FD'
        }}>
          <div style={{
            fontSize: '12px',
            color: '#6B7280',
            fontWeight: 500,
            marginBottom: '4px'
          }}>
            P&L
          </div>
          <div style={{
            fontSize: '18px',
            fontWeight: 700,
            color: pnl >= 0 ? '#059669' : '#DC2626'
          }}>
            {pnl >= 0 ? '+' : ''}${pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap'
      }}>
        {/* Start/Stop Button */}
        <button
          onClick={() => isRunning ? handleStop() : handleStart()}
          disabled={loading}
          style={{
            flex: 1,
            minWidth: '80px',
            padding: '10px 16px',
            backgroundColor: isRunning ? '#EF4444' : '#10B981',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '14px',
            cursor: loading ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px'
          }}
        >
          <span>{isRunning ? '⏹️' : '▶️'}</span>
          <span>{isRunning ? 'Stop' : 'Start'}</span>
        </button>

        {/* Edit Button */}
        <button
          onClick={() => onEdit(bot)}
          style={{
            padding: '10px 16px',
            backgroundColor: '#F3F4F6',
            color: '#374151',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '14px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <span>✏️</span>
          <span>Edit</span>
        </button>

        {/* Delete Button */}
        <button
          onClick={() => setDeleteConfirm(true)}
          style={{
            padding: '10px 16px',
            backgroundColor: 'transparent',
            color: '#EF4444',
            border: '1px solid #EF4444',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '14px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <span>🗑️</span>
          <span>Delete</span>
        </button>
      </div>
    </div>
  );
};
```

---

## 🎨 CSS Animation (Optional)

Add this to your CSS file for spinning refresh icon:

```css
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
```

---

## ✅ Features

1. **Refresh Button**: Small blue button with ↻ icon next to "Balance" header
2. **Loading State**: Shows "Refreshing..." and disables button during fetch
3. **Visual Feedback**: Button changes color on hover, shows loading animation
4. **Error Handling**: Shows error message if refresh fails
5. **Updates Display**: Immediately shows new balance after refresh

---

## 🔄 How It Works

1. **User clicks Refresh** → `handleRefreshBalance()` called
2. **Button shows loading** → `balanceLoading = true`
3. **Fetches from API** → `GET /api/bots/{bot_id}/stats`
4. **Updates state** → `setBalance(data)`
5. **UI updates** → Balance display shows new values
6. **Button resets** → `balanceLoading = false`

---

## 📝 Backend Endpoint

The refresh button calls:
```
GET /api/bots/{bot_id}/stats
```

**Response:**
```json
{
  "available": {
    "SHARP": 8000000,
    "USDT": 1500
  },
  "locked": {
    "SHARP": 0,
    "USDT": 0
  },
  "volume_24h": 5234.50,
  "trades_24h": {
    "buys": 25,
    "sells": 20
  },
  "balance_error": null
}
```

---

## 🚀 Quick Implementation

**If your bot card component already exists**, just add:

1. **State for balance loading**:
```jsx
const [balanceLoading, setBalanceLoading] = useState(false);
const [balance, setBalance] = useState(null);
```

2. **Refresh handler**:
```jsx
const handleRefreshBalance = async () => {
  setBalanceLoading(true);
  try {
    const response = await fetch(`/api/bots/${bot.id}/stats`);
    const data = await response.json();
    setBalance(data);
  } catch (error) {
    alert('Failed to refresh balance');
  } finally {
    setBalanceLoading(false);
  }
};
```

3. **Refresh button** (add next to balance display):
```jsx
<button onClick={handleRefreshBalance} disabled={balanceLoading}>
  {balanceLoading ? '⟳ Refreshing...' : '↻ Refresh'}
</button>
```

---

## ✅ Testing Checklist

- [ ] Refresh button appears on each bot card
- [ ] Click refresh → Button shows "Refreshing..."
- [ ] Balance updates after refresh completes
- [ ] Button re-enables after refresh
- [ ] Error handling works if API fails
- [ ] Loading state shows while fetching
- [ ] Works for both running and stopped bots

---

## 📍 Summary

**What you get:**
- ✅ Refresh button on each bot card
- ✅ Manual balance refresh without page reload
- ✅ Visual feedback during refresh
- ✅ Error handling

**Backend:** Already works - `/api/bots/{bot_id}/stats` endpoint exists
**Frontend:** Add refresh button + handler (code above)

**Time:** ~10 minutes to implement
