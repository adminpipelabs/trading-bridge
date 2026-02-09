/**
 * COMPACT BOT MANAGEMENT UI - Implementation Code
 * 
 * File: ai-trading-ui/src/pages/AdminDashboard.jsx
 * Component: BotManagementView
 * 
 * Changes:
 * 1. Compact table rows (48px height)
 * 2. Alert banner for stopped/stalled bots
 * 3. Filtering and search
 * 4. Icon-only action buttons
 * 5. Inline status badges
 */

import React, { useState, useEffect } from 'react';

// ============================================
// ALERT BANNER COMPONENT
// ============================================
const AlertBanner = ({ bots, onFilterChange }) => {
  const stopped = bots.filter(b => 
    (b.status && b.status.toLowerCase() === 'stopped') ||
    (b.health_status && b.health_status.toLowerCase() === 'stopped')
  ).length;
  
  const stale = bots.filter(b => 
    (b.health_status && b.health_status.toLowerCase() === 'stale') ||
    (b.status && b.status.toLowerCase() === 'stale')
  ).length;
  
  const errors = bots.filter(b => 
    (b.health_status && b.health_status.toLowerCase() === 'error') ||
    (b.status && b.status.toLowerCase() === 'error')
  ).length;
  
  const totalIssues = stopped + stale + errors;
  
  if (totalIssues === 0) return null;
  
  return (
    <div style={{
      padding: '12px 16px',
      backgroundColor: '#fef3c7',
      border: '1px solid #fbbf24',
      borderRadius: '8px',
      marginBottom: '16px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '20px' }}>⚠️</span>
        <span style={{ fontWeight: '600', fontSize: '14px' }}>
          {totalIssues} bot{totalIssues > 1 ? 's' : ''} need attention:
        </span>
        {stopped > 0 && (
          <span style={{ color: '#dc2626', fontSize: '14px', fontWeight: '500' }}>
            {stopped} stopped
          </span>
        )}
        {stale > 0 && (
          <span style={{ color: '#d97706', fontSize: '14px', fontWeight: '500' }}>
            {stale} stale
          </span>
        )}
        {errors > 0 && (
          <span style={{ color: '#dc2626', fontSize: '14px', fontWeight: '500' }}>
            {errors} errors
          </span>
        )}
      </div>
      <button
        onClick={() => onFilterChange('issues')}
        style={{
          padding: '6px 12px',
          backgroundColor: '#f59e0b',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '13px',
          fontWeight: '500',
          whiteSpace: 'nowrap'
        }}
      >
        View Issues
      </button>
    </div>
  );
};

// ============================================
// COMPACT BOT ROW COMPONENT
// ============================================
const CompactBotRow = ({ bot, onStart, onStop, onEdit, onDelete, onRefreshBalance, theme }) => {
  const [balanceLoading, setBalanceLoading] = useState(false);
  const [balance, setBalance] = useState(null);
  
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
  
  // Refresh balance handler
  const handleRefreshBalance = async () => {
    setBalanceLoading(true);
    try {
      const response = await fetch(`/api/bots/${bot.id}/stats`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setBalance(data);
      if (onRefreshBalance) onRefreshBalance(bot.id, data);
    } catch (error) {
      console.error('Failed to refresh balance:', error);
      alert('Failed to refresh balance. Please try again.');
    } finally {
      setBalanceLoading(false);
    }
  };
  
  const getStatusInfo = (bot) => {
    const status = (bot.status || bot.health_status || '').toLowerCase();
    if (status === 'running') return { color: '#10b981', label: 'Running' };
    if (status === 'stopped') return { color: '#ef4444', label: 'Stopped' };
    if (status === 'stale') return { color: '#f59e0b', label: 'Stale' };
    if (status === 'error') return { color: '#dc2626', label: 'Error' };
    return { color: '#6b7280', label: status || 'Unknown' };
  };
  
  const statusInfo = getStatusInfo(bot);
  const isStopped = (bot.status || bot.health_status || '').toLowerCase() === 'stopped';
  const bgColor = theme === 'dark' ? '#1f2937' : '#ffffff';
  const hoverBg = theme === 'dark' ? '#374151' : '#f9fafb';
  const textColor = theme === 'dark' ? '#f3f4f6' : '#111827';
  const mutedColor = theme === 'dark' ? '#9ca3af' : '#6b7280';
  
  // Use balance from state if available, otherwise fallback to bot prop
  const available = balance?.available || bot.available || bot.balance?.available || {};
  const locked = balance?.locked || bot.locked || bot.balance?.locked || {};
  
  return (
    <tr 
      style={{
        height: '48px',
        borderBottom: `1px solid ${theme === 'dark' ? '#374151' : '#e5e7eb'}`,
        backgroundColor: bgColor,
        transition: 'background-color 0.15s ease'
      }}
      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = hoverBg}
      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = bgColor}
    >
      {/* Status Dot */}
      <td style={{ width: '40px', padding: '8px' }}>
        <div style={{
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          backgroundColor: statusInfo.color,
          margin: 'auto'
        }} />
      </td>
      
      {/* Bot Name */}
      <td style={{ padding: '8px', fontWeight: '500', color: textColor }}>
        <div style={{ fontSize: '14px' }}>{bot.name}</div>
      </td>
      
      {/* Type */}
      <td style={{ padding: '8px', fontSize: '13px', color: mutedColor }}>
        {bot.bot_type === 'volume' ? 'Volume' : bot.bot_type === 'spread' ? 'Spread' : '-'}
      </td>
      
      {/* Pair */}
      <td style={{ padding: '8px', fontSize: '13px', color: textColor }}>
        {bot.trading_pair || bot.pair || '-'}
      </td>
      
      {/* Exchange */}
      <td style={{ padding: '8px', fontSize: '13px', color: mutedColor }}>
        {bot.exchange || bot.connector || '-'}
      </td>
      
      {/* Stats (compact) */}
      <td style={{ padding: '8px', fontSize: '12px', color: mutedColor, width: '100px' }}>
        {bot.stats || bot.volume_today ? (
          <span>{bot.stats || `$${bot.volume_today || 0}`}</span>
        ) : (
          <span style={{ color: theme === 'dark' ? '#4b5563' : '#d1d5db' }}>-</span>
        )}
      </td>
      
      {/* Status Badge (inline) */}
      <td style={{ padding: '8px' }}>
        <span style={{
          padding: '3px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: '500',
          backgroundColor: statusInfo.color + '20',
          color: statusInfo.color
        }}>
          {statusInfo.label}
        </span>
      </td>
      
      {/* Actions (icon buttons) */}
      <td style={{ padding: '8px', width: '140px' }}>
        <div style={{ display: 'flex', gap: '4px', justifyContent: 'flex-end' }}>
          {isStopped ? (
            <button
              onClick={() => onStart(bot.id)}
              title="Start Bot"
              style={{
                padding: '6px 8px',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                minWidth: '32px',
                transition: 'opacity 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
              onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
            >
              ▶
            </button>
          ) : (
            <button
              onClick={() => onStop(bot.id)}
              title="Stop Bot"
              style={{
                padding: '6px 8px',
                backgroundColor: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                minWidth: '32px',
                transition: 'opacity 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
              onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
            >
              ⏹
            </button>
          )}
          <button
            onClick={() => onEdit(bot)}
            title="Edit Bot"
            style={{
              padding: '6px 8px',
              backgroundColor: '#6366f1',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              minWidth: '32px',
              transition: 'opacity 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
          >
            ✏️
          </button>
          <button
            onClick={() => onDelete(bot.id)}
            title="Delete Bot"
            style={{
              padding: '6px 8px',
              backgroundColor: '#dc2626',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              minWidth: '32px',
              transition: 'opacity 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
          >
            🗑️
          </button>
        </div>
      </td>
    </tr>
  );
};

// ============================================
// UPDATED BOT MANAGEMENT VIEW
// ============================================
const BotManagementView = () => {
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all', 'running', 'stopped', 'errors', 'issues'
  const [searchQuery, setSearchQuery] = useState('');
  const { theme } = useTheme(); // Assuming you have theme context
  
  // Fetch bots (your existing logic)
  useEffect(() => {
    fetchBots();
    const interval = setInterval(fetchBots, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);
  
  const fetchBots = async () => {
    try {
      const response = await tradingBridge.getBots();
      setBots(response.bots || []);
    } catch (error) {
      console.error('Failed to fetch bots:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Filter bots
  const filteredBots = bots.filter(bot => {
    // Search filter
    if (searchQuery && !bot.name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    
    // Status filter
    const status = (bot.status || bot.health_status || '').toLowerCase();
    if (filter === 'running') return status === 'running';
    if (filter === 'stopped') return status === 'stopped';
    if (filter === 'errors') return status === 'error';
    if (filter === 'issues') {
      return status === 'stopped' || status === 'stale' || status === 'error';
    }
    
    return true; // 'all'
  });
  
  // Handlers
  const handleStartBot = async (botId) => {
    try {
      await tradingBridge.startBot(botId);
      await fetchBots();
    } catch (error) {
      alert(`Failed to start bot: ${error.message}`);
    }
  };
  
  const handleStopBot = async (botId) => {
    try {
      await tradingBridge.stopBot(botId);
      await fetchBots();
    } catch (error) {
      alert(`Failed to stop bot: ${error.message}`);
    }
  };
  
  const handleEditBot = (bot) => {
    // Your edit modal logic
  };
  
  const handleDeleteBot = async (botId) => {
    if (confirm('Are you sure you want to delete this bot?')) {
      try {
        await tradingBridge.deleteBot(botId);
        await fetchBots();
      } catch (error) {
        alert(`Failed to delete bot: ${error.message}`);
      }
    }
  };
  
  if (loading) {
    return <div>Loading bots...</div>;
  }
  
  const bgColor = theme === 'dark' ? '#111827' : '#ffffff';
  const borderColor = theme === 'dark' ? '#374151' : '#e5e7eb';
  const textColor = theme === 'dark' ? '#f3f4f6' : '#111827';
  
  return (
    <div style={{ padding: '24px', backgroundColor: bgColor, minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: textColor, marginBottom: '8px' }}>
          Bot Management
        </h1>
        <p style={{ color: theme === 'dark' ? '#9ca3af' : '#6b7280', fontSize: '14px' }}>
          Create and manage your trading bots
        </p>
      </div>
      
      {/* Alert Banner */}
      <AlertBanner bots={bots} onFilterChange={setFilter} />
      
      {/* Filters and Search */}
      <div style={{ 
        display: 'flex', 
        gap: '12px', 
        marginBottom: '16px',
        alignItems: 'center',
        flexWrap: 'wrap'
      }}>
        {/* Search */}
        <input
          type="text"
          placeholder="Search bots..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            padding: '8px 12px',
            border: `1px solid ${borderColor}`,
            borderRadius: '6px',
            fontSize: '14px',
            flex: 1,
            maxWidth: '300px',
            backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
            color: textColor
          }}
        />
        
        {/* Filter Buttons */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[
            { key: 'all', label: 'All' },
            { key: 'running', label: 'Running' },
            { key: 'stopped', label: 'Stopped' },
            { key: 'errors', label: 'Errors' },
            { key: 'issues', label: 'Issues' }
          ].map(f => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              style={{
                padding: '8px 16px',
                backgroundColor: filter === f.key ? '#6366f1' : (theme === 'dark' ? '#374151' : '#f3f4f6'),
                color: filter === f.key ? 'white' : textColor,
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: filter === f.key ? '600' : '400',
                transition: 'all 0.2s'
              }}
            >
              {f.label} {f.key === 'issues' && `(${bots.filter(b => {
                const s = (b.status || b.health_status || '').toLowerCase();
                return s === 'stopped' || s === 'stale' || s === 'error';
              }).length})`}
            </button>
          ))}
        </div>
        
        {/* Create Bot Button */}
        <button
          onClick={() => {/* Open create modal */}}
          style={{
            padding: '8px 16px',
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            marginLeft: 'auto'
          }}
        >
          + Create Bot
        </button>
      </div>
      
      {/* Compact Table */}
      <div style={{
        border: `1px solid ${borderColor}`,
        borderRadius: '8px',
        overflow: 'hidden',
        backgroundColor: bgColor
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ 
              backgroundColor: theme === 'dark' ? '#1f2937' : '#f9fafb',
              borderBottom: `2px solid ${borderColor}`,
              height: '40px'
            }}>
              <th style={{ width: '40px', padding: '8px', textAlign: 'left' }}></th>
              <th style={{ padding: '8px', textAlign: 'left', fontWeight: '600', fontSize: '13px', color: textColor }}>Name</th>
              <th style={{ padding: '8px', textAlign: 'left', fontWeight: '600', fontSize: '13px', color: textColor }}>Type</th>
              <th style={{ padding: '8px', textAlign: 'left', fontWeight: '600', fontSize: '13px', color: textColor }}>Pair</th>
              <th style={{ padding: '8px', textAlign: 'left', fontWeight: '600', fontSize: '13px', color: textColor }}>Exchange</th>
              <th style={{ padding: '8px', textAlign: 'left', fontWeight: '600', fontSize: '13px', color: textColor, width: '100px' }}>Stats</th>
              <th style={{ padding: '8px', textAlign: 'left', fontWeight: '600', fontSize: '13px', color: textColor }}>Status</th>
              <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', fontSize: '13px', color: textColor, width: '140px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredBots.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ padding: '32px', textAlign: 'center', color: mutedColor }}>
                  {searchQuery ? 'No bots found matching your search' : 'No bots found'}
                </td>
              </tr>
            ) : (
              filteredBots.map(bot => (
                <CompactBotRow
                  key={bot.id}
                  bot={bot}
                  onStart={handleStartBot}
                  onStop={handleStopBot}
                  onEdit={handleEditBot}
                  onDelete={handleDeleteBot}
                  theme={theme}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Results Count */}
      <div style={{ 
        marginTop: '12px', 
        fontSize: '13px', 
        color: theme === 'dark' ? '#9ca3af' : '#6b7280' 
      }}>
        Showing {filteredBots.length} of {bots.length} bots
      </div>
    </div>
  );
};

export default BotManagementView;
