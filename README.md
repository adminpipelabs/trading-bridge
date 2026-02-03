# Bot Health Monitor — Pipe Labs Trading Bridge

## Problem
Bot status in PostgreSQL only updates when explicitly set via API (`/bots/{id}/start` or `/bots/{id}/stop`). If a bot crashes, Hummingbot goes down, or the exchange disconnects, the dashboard still shows "running."

## Solution
A background health monitoring system that runs inside trading-bridge and verifies bot status by checking actual trade activity on the exchange.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  BotHealthMonitor (background asyncio task)          │
│                                                       │
│  Every 5 min:                                         │
│  1. Query all bots where status = 'running'           │
│  2. For each bot, fetch recent trades via ccxt         │
│  3. Evaluate trade recency:                           │
│     • Trades < 30 min ago  → healthy ✅               │
│     • Trades 30m-2h ago    → stale ⚠️                │
│     • No trades > 2h       → stopped 🔴              │
│  4. Update bots table + log to bot_health_logs        │
└──────────────────────────────────────────────────────┘
         │                              ▲
         ▼                              │
┌─────────────┐              ┌──────────────────┐
│  PostgreSQL  │              │  BitMart (ccxt)  │
│  bots table  │              │  fetch_my_trades │
│  health_logs │              └──────────────────┘
└─────────────┘
         ▲
         │
┌──────────────────────────────────────────────────────┐
│  Health API Routes                                    │
│                                                       │
│  GET  /bots/{id}/health        → single bot health   │
│  POST /bots/{id}/health/check  → force recheck now   │
│  GET  /bots/health/summary     → all bots overview   │
│  POST /bots/heartbeat          → receive heartbeat   │
│  GET  /bots/{id}/health/history → audit trail        │
└──────────────────────────────────────────────────────┘
```

## Files

| File | Purpose | Add To |
|------|---------|--------|
| `migrations/add_bot_health_tracking.sql` | DB schema changes | Run against Railway PostgreSQL |
| `app/bot_health.py` | Core monitoring service | `trading-bridge/app/bot_health.py` |
| `app/health_routes.py` | API endpoints | `trading-bridge/app/health_routes.py` |
| `app/integration_example.py` | Wiring into main.py | Merge into existing `main.py` |

## Setup Steps

### 1. Run the migration
```bash
# Connect to your Railway PostgreSQL and run:
psql $DATABASE_URL -f migrations/add_bot_health_tracking.sql
```

### 2. Add files to trading-bridge
Copy `bot_health.py` and `health_routes.py` into your `app/` directory.

### 3. Update main.py
Follow `integration_example.py` to:
- Import and register health routes
- Start/stop the health monitor on app lifecycle
- Update existing start/stop bot endpoints to set `reported_status`

### 4. Deploy to Railway
```bash
git add .
git commit -m "feat: add bot health monitoring"
git push
```

### 5. Verify
```bash
# Check health summary
curl https://trading-bridge-production.up.railway.app/bots/health/summary

# Check specific bot
curl https://trading-bridge-production.up.railway.app/bots/1/health

# Force immediate check
curl -X POST https://trading-bridge-production.up.railway.app/bots/1/health/check
```

## Thresholds (Configurable)

| Setting | Default | Purpose |
|---------|---------|---------|
| `HEALTH_CHECK_INTERVAL_SECONDS` | 300 (5 min) | How often to run checks |
| `STALE_THRESHOLD_MINUTES` | 30 | No trades → mark as stale |
| `STOPPED_THRESHOLD_MINUTES` | 120 (2h) | No trades → mark as stopped |
| `HEARTBEAT_TIMEOUT_MINUTES` | 15 | Heartbeat too old → check trades |

Adjust in `bot_health.py` based on your trading pair's typical volume. For low-volume pairs like SHARP/USDT, you may want to increase the stale threshold.

## Health Statuses

| Status | Meaning | Dashboard Display |
|--------|---------|-------------------|
| `healthy` | Recent trades confirmed | 🟢 Running |
| `stale` | No recent trades, might be normal | 🟡 Running (stale) |
| `stopped` | No trades beyond threshold, likely dead | 🔴 Stopped |
| `error` | Health check itself failed | ⚠️ Unknown |
| `unknown` | Not yet checked or no credentials | ⚪ Unknown |

## Frontend Integration

Update the dashboard to use health_status for display:

```javascript
// In your bot status component, use health_status instead of just status
const getStatusBadge = (bot) => {
  const { status, health_status } = bot;
  
  if (health_status === 'healthy') return { color: 'green', label: 'Running' };
  if (health_status === 'stale') return { color: 'yellow', label: 'Stale' };
  if (health_status === 'stopped') return { color: 'red', label: 'Stopped' };
  if (health_status === 'error') return { color: 'orange', label: 'Error' };
  return { color: 'gray', label: 'Unknown' };
};

// Add a "Refresh" button that calls the force-check endpoint
const refreshBotHealth = async (botId) => {
  const res = await fetch(`/bots/${botId}/health/check`, { method: 'POST' });
  return res.json();
};
```

## Future: Hummingbot Heartbeat Push

When ready, add a simple script alongside Hummingbot that pushes heartbeats:

```python
# hummingbot_heartbeat.py — run as a sidecar or cron
import requests, time

BOT_ID = 1
BRIDGE_URL = "https://trading-bridge-production.up.railway.app"

while True:
    try:
        requests.post(f"{BRIDGE_URL}/bots/heartbeat", json={
            "bot_id": BOT_ID,
            "status": "running",
            "metadata": {"timestamp": time.time()}
        })
    except Exception:
        pass
    time.sleep(60)  # Every minute
```

## Also Fixes: Hardcoded "Active Bots: 34"

The `/bots/health/summary` endpoint returns real counts. Replace the hardcoded stat on the dashboard:

```javascript
// Before (hardcoded)
const activeBots = 34;

// After (real data)
const { data } = await fetch('/bots/health/summary?account=client_sharp');
const activeBots = data.healthy + data.stale; // Actually running bots
```

This kills two birds with one stone — accurate bot status AND accurate bot counts.
