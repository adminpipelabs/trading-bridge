# Frontend Integration Guide - Complete Implementation

## 🎯 What Frontend Needs to Do

Connect the client dashboard to the backend bot endpoints to display:
- Bot list with balances
- Available/Locked funds
- Volume
- P&L
- Start/Stop/Edit/Delete actions

---

## 📋 Files to Update

### 1. **API Service** (`ai-trading-ui/src/services/api.js` or similar)

Add bot-related API calls:

```javascript
// Add to your API service file
const API_BASE = process.env.REACT_APP_API_URL || 'https://your-api.com';

export const tradingBridge = {
  // List bots with balances
  async getBots(account, walletAddress) {
    const response = await fetch(
      `${API_BASE}/bots?account=${account}&include_balances=true`,
      {
        headers: {
          'X-Wallet-Address': walletAddress,
          'Content-Type': 'application/json'
        }
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch bots: ${response.statusText}`);
    }
    return response.json();
  },

  // Get bot balance and volume
  async getBotBalance(botId) {
    const response = await fetch(`${API_BASE}/bots/${botId}/balance-and-volume`);
    if (!response.ok) {
      throw new Error(`Failed to fetch balance: ${response.statusText}`);
    }
    return response.json();
  },

  // Start bot
  async startBot(botId, walletAddress) {
    const response = await fetch(`${API_BASE}/bots/${botId}/start`, {
      method: 'POST',
      headers: {
        'X-Wallet-Address': walletAddress,
        'Content-Type': 'application/json'
      }
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start bot');
    }
    return response.json();
  },

  // Stop bot
  async stopBot(botId, walletAddress) {
    const response = await fetch(`${API_BASE}/bots/${botId}/stop`, {
      method: 'POST',
      headers: {
        'X-Wallet-Address': walletAddress,
        'Content-Type': 'application/json'
      }
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to stop bot');
    }
    return response.json();
  },

  // Delete bot
  async deleteBot(botId, walletAddress) {
    const response = await fetch(`${API_BASE}/bots/${botId}`, {
      method: 'DELETE',
      headers: {
        'X-Wallet-Address': walletAddress,
        'Content-Type': 'application/json'
      }
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete bot');
    }
    return response.json();
  },

  // Add exchange credentials to bot
  async addBotCredentials(botId, apiKey, apiSecret, passphrase, walletAddress) {
    const params = new URLSearchParams({
      api_key: apiKey,
      api_secret: apiSecret
    });
    if (passphrase) {
      params.append('passphrase', passphrase);
    }
    
    const response = await fetch(
      `${API_BASE}/bots/${botId}/add-exchange-credentials?${params}`,
      {
        method: 'POST',
        headers: {
          'X-Wallet-Address': walletAddress,
          'Content-Type': 'application/json'
        }
      }
    );
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to add credentials');
    }
    return response.json();
  }
};
```

---

### 2. **Bot Card Component** (`ai-trading-ui/src/components/BotCard.jsx`)

Create compact bot card component:

```jsx
import React, { useState } from 'react';
import { tradingBridge } from '../services/api';

const BotCard = ({ bot, walletAddress, account, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const isRunning = bot.status === 'running';
  
  // Format numbers compactly
  const formatCompact = (num) => {
    if (num === 0) return '0';
    if (num < 0.01) return '<0.01';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    if (num >= 1) return num.toFixed(2);
    return num.toFixed(4);
  };

  const handleStart = async () => {
    try {
      setLoading(true);
      await tradingBridge.startBot(bot.id, walletAddress);
      onUpdate(); // Refresh bot list
    } catch (error) {
      alert(`Failed to start bot: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      setLoading(true);
      await tradingBridge.stopBot(bot.id, walletAddress);
      onUpdate(); // Refresh bot list
    } catch (error) {
      alert(`Failed to stop bot: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      setLoading(true);
      await tradingBridge.deleteBot(bot.id, walletAddress);
      setDeleteConfirm(false);
      onUpdate(); // Refresh bot list
    } catch (error) {
      alert(`Failed to delete bot: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Get available/locked from bot data
  const available = bot.available || bot.balance?.available || {};
  const locked = bot.locked || bot.balance?.locked || {};
  const volume = bot.volume?.value_usd || bot.balance?.volume_24h || 0;
  const pnl = bot.pnl?.total_usd || 0;

  return (
    <>
      <div style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid #E5E7EB',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '12px',
        boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '10px'
        }}>
          <h3 style={{
            margin: 0,
            fontSize: '16px',
            fontWeight: 700,
            color: '#111827',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {bot.name}
          </h3>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '3px 10px',
            backgroundColor: isRunning ? '#D1FAE5' : '#F3F4F6',
            color: isRunning ? '#059669' : '#6B7280',
            borderRadius: '16px',
            fontSize: '11px',
            fontWeight: 600
          }}>
            <span style={{ fontSize: '8px' }}>{isRunning ? '●' : '○'}</span>
            <span>{isRunning ? 'Running' : 'Stopped'}</span>
          </div>
        </div>

        {/* Warning Messages */}
        {bot.health_message && (
          <div style={{
            padding: '8px 10px',
            backgroundColor: bot.health_message.includes('Missing API') 
              ? '#FEF3C7' 
              : '#DBEAFE',
            border: `1px solid ${bot.health_message.includes('Missing API') 
              ? '#FBBF24' 
              : '#60A5FA'}`,
            borderRadius: '6px',
            marginBottom: '10px',
            fontSize: '12px'
          }}>
            <div style={{
              fontWeight: 600,
              fontSize: '12px',
              color: bot.health_message.includes('Missing API') 
                ? '#92400E' 
                : '#1E40AF',
              marginBottom: '2px'
            }}>
              {bot.health_message.includes('Missing API') 
                ? '⚠️ Connect API Keys' 
                : '⚠️ Action Needed'}
            </div>
            <div style={{
              fontSize: '11px',
              color: bot.health_message.includes('Missing API') 
                ? '#78350F' 
                : '#1E3A8A'
            }}>
              {bot.health_message.includes('Missing API')
                ? 'Click Edit to add keys'
                : bot.health_message}
            </div>
          </div>
        )}

        {/* Financial Info Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '8px',
          marginBottom: '12px'
        }}>
          {/* Available */}
          <div style={{
            padding: '8px',
            backgroundColor: '#F9FAFB',
            borderRadius: '6px'
          }}>
            <div style={{
              fontSize: '10px',
              color: '#6B7280',
              fontWeight: 600,
              textTransform: 'uppercase',
              marginBottom: '4px'
            }}>
              Available
            </div>
            {Object.keys(available).length > 0 && Object.values(available).some(v => v > 0) ? (
              <div>
                {Object.entries(available).map(([asset, amount]) => {
                  if (amount <= 0) return null;
                  return (
                    <div key={asset} style={{
                      fontSize: '12px',
                      fontWeight: 600,
                      color: '#111827',
                      marginBottom: '2px'
                    }}>
                      {formatCompact(amount)} {asset}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ fontSize: '10px', color: '#9CA3AF' }}>N/A</div>
            )}
          </div>

          {/* Locked */}
          <div style={{
            padding: '8px',
            backgroundColor: '#F9FAFB',
            borderRadius: '6px'
          }}>
            <div style={{
              fontSize: '10px',
              color: '#6B7280',
              fontWeight: 600,
              textTransform: 'uppercase',
              marginBottom: '4px'
            }}>
              Locked
            </div>
            {Object.keys(locked).length > 0 && Object.values(locked).some(v => v > 0) ? (
              <div>
                {Object.entries(locked).map(([asset, amount]) => {
                  if (amount <= 0) return null;
                  return (
                    <div key={asset} style={{
                      fontSize: '12px',
                      fontWeight: 600,
                      color: '#111827',
                      marginBottom: '2px'
                    }}>
                      {formatCompact(amount)} {asset}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ fontSize: '10px', color: '#9CA3AF' }}>0</div>
            )}
          </div>

          {/* Volume */}
          <div style={{
            padding: '8px',
            backgroundColor: '#F0FDF4',
            borderRadius: '6px',
            border: '1px solid #86EFAC'
          }}>
            <div style={{
              fontSize: '10px',
              color: '#6B7280',
              fontWeight: 600,
              textTransform: 'uppercase',
              marginBottom: '4px'
            }}>
              Volume
            </div>
            <div style={{
              fontSize: '16px',
              fontWeight: 700,
              color: '#059669'
            }}>
              ${formatCompact(volume)}
            </div>
          </div>

          {/* P&L */}
          <div style={{
            padding: '8px',
            backgroundColor: pnl >= 0 ? '#F0FDF4' : '#FEE2E2',
            borderRadius: '6px',
            border: `1px solid ${pnl >= 0 ? '#86EFAC' : '#FCA5A5'}`
          }}>
            <div style={{
              fontSize: '10px',
              color: '#6B7280',
              fontWeight: 600,
              textTransform: 'uppercase',
              marginBottom: '4px'
            }}>
              P&L
            </div>
            <div style={{
              fontSize: '16px',
              fontWeight: 700,
              color: pnl >= 0 ? '#059669' : '#DC2626'
            }}>
              {pnl >= 0 ? '+' : ''}${formatCompact(pnl)}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{
          display: 'flex',
          gap: '6px',
          flexWrap: 'wrap'
        }}>
          <button
            onClick={isRunning ? handleStop : handleStart}
            disabled={loading}
            style={{
              flex: 1,
              minWidth: '80px',
              padding: '8px 12px',
              backgroundColor: isRunning ? '#EF4444' : '#10B981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '13px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px'
            }}
          >
            <span style={{ fontSize: '12px' }}>{isRunning ? '⏹️' : '▶️'}</span>
            <span>{loading ? '...' : (isRunning ? 'Stop' : 'Start')}</span>
          </button>

          <button
            onClick={() => {/* Open edit modal */}}
            style={{
              padding: '8px 12px',
              backgroundColor: '#F3F4F6',
              color: '#374151',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <span style={{ fontSize: '12px' }}>✏️</span>
            <span>Edit</span>
          </button>

          <button
            onClick={() => setDeleteConfirm(true)}
            style={{
              padding: '8px 12px',
              backgroundColor: 'transparent',
              color: '#EF4444',
              border: '1px solid #EF4444',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <span style={{ fontSize: '12px' }}>🗑️</span>
            <span>Delete</span>
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
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
        onClick={() => setDeleteConfirm(false)}
        >
          <div 
            style={{
              backgroundColor: 'white',
              padding: '24px',
              borderRadius: '12px',
              maxWidth: '400px',
              width: '90%'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginBottom: '16px' }}>Delete Bot?</h3>
            <p style={{ color: '#6B7280', marginBottom: '24px' }}>
              Are you sure you want to delete <strong>"{bot.name}"</strong>?
              This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button onClick={() => setDeleteConfirm(false)}>
                Cancel
              </button>
              <button 
                onClick={handleDelete}
                disabled={loading}
                style={{ backgroundColor: '#EF4444', color: 'white' }}
              >
                {loading ? 'Deleting...' : 'Delete Bot'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default BotCard;
```

---

### 3. **Bot List Component** (`ai-trading-ui/src/components/BotList.jsx`)

Create responsive bot list container:

```jsx
import React, { useState, useEffect } from 'react';
import BotCard from './BotCard';
import { tradingBridge } from '../services/api';

const BotList = ({ account, walletAddress }) => {
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBots = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await tradingBridge.getBots(account, walletAddress);
      setBots(data.bots || []);
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch bots:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBots();
    // Refresh every 30 seconds
    const interval = setInterval(fetchBots, 30000);
    return () => clearInterval(interval);
  }, [account, walletAddress]);

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div>Loading bots...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#EF4444' }}>
        <div>Error: {error}</div>
        <button onClick={fetchBots} style={{ marginTop: '16px' }}>
          Retry
        </button>
      </div>
    );
  }

  if (bots.length === 0) {
    return (
      <div style={{
        padding: '60px 20px',
        textAlign: 'center',
        color: '#6B7280'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🤖</div>
        <div style={{ fontSize: '20px', fontWeight: 600, marginBottom: '8px' }}>
          No Bots Yet
        </div>
        <div style={{ fontSize: '14px' }}>
          Create your first bot to start trading
        </div>
      </div>
    );
  }

  return (
    <div style={{
      padding: '12px',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px'
    }}
    // Responsive grid for desktop
    className="bot-list-container"
    >
      {bots.map(bot => (
        <BotCard
          key={bot.id}
          bot={bot}
          walletAddress={walletAddress}
          account={account}
          onUpdate={fetchBots}
        />
      ))}
    </div>
  );
};

// Add CSS for responsive grid (in your CSS file or styled-components)
// @media (min-width: 768px) {
//   .bot-list-container {
//     display: grid;
//     grid-template-columns: repeat(2, 1fr);
//     gap: 12px;
//   }
// }
// @media (min-width: 1024px) {
//   .bot-list-container {
//     grid-template-columns: repeat(3, 1fr);
//   }
// }

export default BotList;
```

---

### 4. **Update Client Dashboard** (`ai-trading-ui/src/pages/ClientDashboard.jsx`)

Replace bot list section:

```jsx
import BotList from '../components/BotList';

// In your ClientDashboard component:
<BotList 
  account={client.account_identifier}
  walletAddress={walletAddress} // Get from auth context
/>
```

---

## 📋 Integration Checklist

### Step 1: API Service ✅
- [ ] Add `tradingBridge` object to API service
- [ ] Add all bot-related methods (getBots, startBot, stopBot, deleteBot, etc.)
- [ ] Test API calls work

### Step 2: Bot Card Component ✅
- [ ] Create `BotCard.jsx` component
- [ ] Add compact styling
- [ ] Add action handlers (start/stop/delete)
- [ ] Add delete confirmation modal

### Step 3: Bot List Component ✅
- [ ] Create `BotList.jsx` container
- [ ] Add auto-refresh (every 30 seconds)
- [ ] Add loading/error states
- [ ] Add empty state

### Step 4: Update Dashboard ✅
- [ ] Import `BotList` component
- [ ] Replace existing bot display
- [ ] Pass `account` and `walletAddress` props

### Step 5: Test ✅
- [ ] Test bot list loads
- [ ] Test balances display
- [ ] Test start/stop buttons
- [ ] Test delete with confirmation
- [ ] Test on mobile and desktop

---

## 🎯 Expected Result

**Mobile:**
- Single column of compact bot cards
- All info visible
- Touch-friendly buttons

**Desktop:**
- Grid layout (2-3 columns)
- More bots visible at once
- Professional appearance

---

## ✅ Summary

**What to do:**
1. Copy API service code → Add to your API file
2. Copy BotCard component → Create new file
3. Copy BotList component → Create new file
4. Update ClientDashboard → Import and use BotList

**Time:** ~2-3 hours to implement and test

**Result:** Fully functional bot dashboard with all features!
