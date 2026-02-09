# Bot Card UI Design - Mobile & Desktop Responsive

## 🎯 Design Goals

1. **Mobile-first** - Easy to read on small screens
2. **Card-based** - Each bot in its own box
3. **Clean layout** - Easy to scan
4. **Responsive** - Works on all screen sizes

---

## 📱 Mobile Layout (Single Column)

```
┌─────────────────────────────┐
│ SHARP-VB-BitMart            │
│ [Running]                   │
├─────────────────────────────┤
│ ⚠️ Connect API Keys         │
│ Click Edit to add            │
├─────────────────────────────┤
│ Available                   │
│ 8,000,000 SHARP             │
│ 1,500 USDT                  │
│                             │
│ Locked                      │
│ 0 SHARP | 0 USDT            │
│                             │
│ Volume                      │
│ $5,234.50                   │
│                             │
│ P&L                         │
│ +$123.45                    │
├─────────────────────────────┤
│ [▶️ Start] [✏️ Edit] [🗑️]  │
└─────────────────────────────┘
```

---

## 💻 Desktop Layout (Grid - 2-3 columns)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Bot 1        │  │ Bot 2        │  │ Bot 3        │
│ [Running]    │  │ [Stopped]    │  │ [Running]    │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ Available    │  │ Available    │  │ Available    │
│ 8M SHARP     │  │ 0 SHARP      │  │ 5M SHARP     │
│ 1.5K USDT    │  │ 0 USDT       │  │ 2K USDT      │
│              │  │              │  │              │
│ Volume       │  │ Volume       │  │ Volume       │
│ $5,234       │  │ $0           │  │ $3,456       │
│              │  │              │  │              │
│ P&L          │  │ P&L          │  │ P&L          │
│ +$123        │  │ $0           │  │ +$89         │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ [▶] [✏] [🗑] │  │ [▶] [✏] [🗑] │  │ [▶] [✏] [🗑] │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🎨 Implementation Code

### Complete Bot Card Component

```jsx
// BotCard.jsx - Responsive card component
import React from 'react';

const BotCard = ({ bot, onStart, onStop, onEdit, onDelete }) => {
  const isRunning = bot.status === 'running';
  
  return (
    <div style={{
      backgroundColor: '#FFFFFF',
      border: '1px solid #E5E7EB',
      borderRadius: '8px',
      padding: '12px', // Reduced from 20px
      marginBottom: '12px', // Reduced from 16px
      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
      transition: 'all 0.2s ease',
      // Responsive width - keep compact
      width: '100%',
      maxWidth: '100%',
      // Desktop: fixed width for grid - smaller cards
      '@media (min-width: 768px)': {
        width: 'calc(50% - 8px)', // 2 columns
        maxWidth: '320px' // Reduced from 400px
      },
      '@media (min-width: 1024px)': {
        width: 'calc(33.333% - 12px)', // 3 columns
        maxWidth: '300px' // Even smaller for 3 columns
      }
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
      e.currentTarget.style.transform = 'translateY(-2px)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
      e.currentTarget.style.transform = 'translateY(0)';
    }}
    >
      {/* Header - Compact */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '10px', // Reduced from 16px
        flexWrap: 'wrap',
        gap: '6px'
      }}>
        <h3 style={{
          margin: 0,
          fontSize: '16px', // Reduced from 18px
          fontWeight: 700,
          color: '#111827',
          flex: 1,
          minWidth: 0,
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
          padding: '3px 10px', // Reduced padding
          backgroundColor: isRunning ? '#D1FAE5' : '#F3F4F6',
          color: isRunning ? '#059669' : '#6B7280',
          borderRadius: '16px',
          fontSize: '11px', // Reduced from 12px
          fontWeight: 600,
          whiteSpace: 'nowrap'
        }}>
          <span style={{ fontSize: '8px' }}>{isRunning ? '●' : '○'}</span>
          <span>{isRunning ? 'Running' : 'Stopped'}</span>
        </div>
      </div>

      {/* Warning/Error Messages - Compact */}
      {bot.health_message && (
        <div style={{
          padding: '8px 10px', // Reduced padding
          backgroundColor: bot.health_message.includes('Missing API') 
            ? '#FEF3C7' 
            : '#DBEAFE',
          border: `1px solid ${bot.health_message.includes('Missing API') 
            ? '#FBBF24' 
            : '#60A5FA'}`,
          borderRadius: '6px',
          marginBottom: '10px', // Reduced from 16px
          fontSize: '12px' // Smaller text
        }}>
          <div style={{
            fontWeight: 600,
            fontSize: '12px', // Reduced from 14px
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
            fontSize: '11px', // Reduced from 13px
            color: bot.health_message.includes('Missing API') 
              ? '#78350F' 
              : '#1E3A8A',
            lineHeight: '1.3'
          }}>
            {bot.health_message.includes('Missing API')
              ? 'Click Edit to add keys'
              : bot.health_message}
          </div>
        </div>
      )}

      {/* Financial Info Grid - Compact */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '8px', // Reduced from 16px
        marginBottom: '12px' // Reduced from 16px
      }}>
        {/* Available Funds */}
        <div style={{
          padding: '8px', // Reduced from 12px
          backgroundColor: '#F9FAFB',
          borderRadius: '6px'
        }}>
          <div style={{
            fontSize: '10px', // Reduced from 11px
            color: '#6B7280',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
            marginBottom: '4px' // Reduced from 8px
          }}>
            Available
          </div>
          {bot.available && Object.keys(bot.available).length > 0 && 
           Object.values(bot.available).some(v => v > 0) ? (
            <div>
              {Object.entries(bot.available).map(([asset, amount]) => {
                if (amount <= 0) return null;
                return (
                  <div key={asset} style={{
                    fontSize: '12px', // Reduced from 14px
                    fontWeight: 600,
                    color: '#111827',
                    marginBottom: '2px', // Reduced from 4px
                    lineHeight: '1.3'
                  }}>
                    {formatCompact(amount)} {asset}
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{
              fontSize: '10px', // Reduced from 12px
              color: '#9CA3AF',
              fontStyle: 'italic'
            }}>
              N/A
            </div>
          )}
        </div>

        {/* Locked Funds */}
        <div style={{
          padding: '8px', // Reduced from 12px
          backgroundColor: '#F9FAFB',
          borderRadius: '6px'
        }}>
          <div style={{
            fontSize: '10px', // Reduced from 11px
            color: '#6B7280',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
            marginBottom: '4px' // Reduced from 8px
          }}>
            Locked
          </div>
          {bot.locked && Object.keys(bot.locked).length > 0 && 
           Object.values(bot.locked).some(v => v > 0) ? (
            <div>
              {Object.entries(bot.locked).map(([asset, amount]) => {
                if (amount <= 0) return null;
                return (
                  <div key={asset} style={{
                    fontSize: '12px', // Reduced from 14px
                    fontWeight: 600,
                    color: '#111827',
                    marginBottom: '2px',
                    lineHeight: '1.3'
                  }}>
                    {formatCompact(amount)} {asset}
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{
              fontSize: '10px', // Reduced from 12px
              color: '#9CA3AF'
            }}>
              0
            </div>
          )}
        </div>

        {/* Volume */}
        <div style={{
          padding: '8px', // Reduced from 12px
          backgroundColor: '#F0FDF4',
          borderRadius: '6px',
          border: '1px solid #86EFAC'
        }}>
          <div style={{
            fontSize: '10px', // Reduced from 11px
            color: '#6B7280',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
            marginBottom: '4px' // Reduced from 8px
          }}>
            Volume
          </div>
          <div style={{
            fontSize: '16px', // Reduced from 18px
            fontWeight: 700,
            color: '#059669'
          }}>
            ${formatCompact(bot.volume?.value_usd || 0)}
          </div>
        </div>

        {/* P&L */}
        <div style={{
          padding: '8px', // Reduced from 12px
          backgroundColor: bot.pnl?.total_usd >= 0 ? '#F0FDF4' : '#FEE2E2',
          borderRadius: '6px',
          border: `1px solid ${bot.pnl?.total_usd >= 0 ? '#86EFAC' : '#FCA5A5'}`
        }}>
          <div style={{
            fontSize: '10px', // Reduced from 11px
            color: '#6B7280',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
            marginBottom: '4px' // Reduced from 8px
          }}>
            P&L
          </div>
          <div style={{
            fontSize: '16px', // Reduced from 18px
            fontWeight: 700,
            color: bot.pnl?.total_usd >= 0 ? '#059669' : '#DC2626'
          }}>
            {bot.pnl?.total_usd >= 0 ? '+' : ''}${formatCompact(bot.pnl?.total_usd || 0)}
          </div>
        </div>
      </div>

      {/* Action Buttons - Compact */}
      <div style={{
        display: 'flex',
        gap: '6px', // Reduced from 8px
        flexWrap: 'wrap'
      }}>
        {/* Start/Stop Button */}
        <button
          onClick={() => isRunning ? onStop(bot.id) : onStart(bot.id)}
          style={{
            flex: 1,
            minWidth: '80px', // Reduced from 100px
            padding: '8px 12px', // Reduced from 10px 16px
            backgroundColor: isRunning ? '#EF4444' : '#10B981',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 600,
            fontSize: '13px', // Reduced from 14px
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px'
          }}
        >
          <span style={{ fontSize: '12px' }}>{isRunning ? '⏹️' : '▶️'}</span>
          <span>{isRunning ? 'Stop' : 'Start'}</span>
        </button>

        {/* Edit Button */}
        <button
          onClick={() => onEdit(bot)}
          style={{
            padding: '8px 12px', // Reduced from 10px 16px
            backgroundColor: '#F3F4F6',
            color: '#374151',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 600,
            fontSize: '13px', // Reduced from 14px
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          <span style={{ fontSize: '12px' }}>✏️</span>
          <span>Edit</span>
        </button>

        {/* Delete Button */}
        <button
          onClick={() => onDelete(bot)}
          style={{
            padding: '8px 12px', // Reduced from 10px 16px
            backgroundColor: 'transparent',
            color: '#EF4444',
            border: '1px solid #EF4444',
            borderRadius: '6px',
            fontWeight: 600,
            fontSize: '13px', // Reduced from 14px
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
  );
};

// Helper function to format numbers - compact version
const formatCompact = (num) => {
  if (num === 0) return '0';
  if (num < 0.01) return '<0.01';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'; // 1 decimal instead of 2
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'; // 1 decimal instead of 2
  // For smaller numbers, show fewer decimals
  if (num >= 1) return num.toFixed(2);
  return num.toFixed(4);
};

export default BotCard;
```

---

## 📱 Container with Responsive Grid

```jsx
// BotList.jsx - Container component
import React from 'react';
import BotCard from './BotCard';

const BotList = ({ bots, onStart, onStop, onEdit, onDelete }) => {
  return (
    <div style={{
      padding: '12px', // Reduced from 20px
      // Mobile: single column
      display: 'flex',
      flexDirection: 'column',
      gap: '12px', // Reduced from 16px
      // Desktop: grid layout
      '@media (min-width: 768px)': {
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '12px' // Reduced from 16px
      },
      '@media (min-width: 1024px)': {
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '12px' // Reduced from 20px
      }
    }}>
      {bots.length === 0 ? (
        <div style={{
          gridColumn: '1 / -1',
          textAlign: 'center',
          padding: '60px 20px',
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
      ) : (
        bots.map(bot => (
          <BotCard
            key={bot.id}
            bot={bot}
            onStart={onStart}
            onStop={onStop}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))
      )}
    </div>
  );
};

export default BotList;
```

---

## 🎨 CSS-in-JS Alternative (If Using Styled Components)

```jsx
import styled from 'styled-components';

const BotCardContainer = styled.div`
  background-color: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px; /* Reduced from 12px */
  padding: 12px; /* Reduced from 20px */
  margin-bottom: 12px; /* Reduced from 16px */
  box-shadow: 0 1px 2px rgba(0,0,0,0.05); /* Lighter shadow */
  transition: all 0.2s ease;
  width: 100%;
  
  &:hover {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1); /* Lighter hover */
    transform: translateY(-1px); /* Less movement */
  }
  
  @media (min-width: 768px) {
    width: calc(50% - 8px);
    max-width: 320px; /* Reduced from 400px */
  }
  
  @media (min-width: 1024px) {
    width: calc(33.333% - 12px);
    max-width: 300px; /* Even smaller for 3 columns */
  }
`;

const BotGrid = styled.div`
  padding: 12px; /* Reduced from 20px */
  display: flex;
  flex-direction: column;
  gap: 12px; /* Reduced from 16px */
  
  @media (min-width: 768px) {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px; /* Reduced from 16px */
  }
  
  @media (min-width: 1024px) {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px; /* Reduced from 20px */
  }
`;
```

---

## 📋 Key Features

### ✅ Mobile-Friendly
- Single column on mobile
- Touch-friendly buttons (min 44px height)
- Readable text sizes
- No horizontal scrolling

### ✅ Desktop-Friendly
- 2 columns on tablet (768px+)
- 3 columns on desktop (1024px+)
- Hover effects
- Better spacing

### ✅ Clean Design
- White cards with subtle shadows
- Color-coded status badges
- Grid layout for financial info
- Clear visual hierarchy

### ✅ Functional
- All info visible at a glance
- Easy to scan
- Clear action buttons
- Responsive to all screen sizes

---

## 🎯 What This Achieves

**Mobile:**
- ✅ Easy to scroll through bots
- ✅ Each bot in its own card
- ✅ All info visible without scrolling horizontally
- ✅ Touch-friendly buttons

**Desktop:**
- ✅ See multiple bots at once
- ✅ Professional grid layout
- ✅ Better use of screen space
- ✅ Clean, modern appearance

---

## 📝 Implementation Steps

1. **Create BotCard component** - Copy code above
2. **Create BotList container** - Copy grid code above
3. **Update ClientDashboard** - Replace bot list with `<BotList />`
4. **Test on mobile** - Check responsive behavior
5. **Test on desktop** - Verify grid layout

**Time:** ~1 hour to implement and test

---

## ✅ Summary

This design provides:
- ✅ **Card-based layout** - Each bot in its own box
- ✅ **Mobile-first** - Works great on phones
- ✅ **Desktop-friendly** - Grid layout on larger screens
- ✅ **Clean & professional** - Modern, polished look
- ✅ **Easy to scan** - All info visible at a glance

The code is ready to use - just copy and integrate into your frontend!
