# Production Documentation - Trading Bridge

**Last Updated:** February 10, 2026  
**Status:** ✅ Production  
**Environment:** Hetzner VPS + Railway PostgreSQL

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Flows](#system-flows)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Code Organization](#code-organization)
6. [Error Handling & Known Issues](#error-handling--known-issues)
7. [Deployment & Infrastructure](#deployment--infrastructure)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Change Log](#change-log)

---

## 🏗️ Architecture Overview

### **System Components**

```
┌─────────────────┐
│  Frontend (UI)  │  Next.js 16, React 19, TypeScript
│  Railway/Vercel │  https://app.pipelabs.xyz
└────────┬────────┘
         │ HTTPS API Calls
         ▼
┌─────────────────┐
│  Trading Bridge │  FastAPI, Python 3.12
│  Backend (API)  │  Hetzner VPS (5.161.64.209:8080)
└────────┬────────┘
         │
    ┌────┴────┬──────────────┬─────────────┐
    ▼         ▼              ▼             ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Postgres│ │Coinstore │ │ BitMart  │ │  Other   │
│Railway │ │   API    │ │   API    │ │ Exchanges│
└────────┘ └──────────┘ └──────────┘ └──────────┘
```

### **Key Services**

1. **Backend API** (`app/main.py`)
   - FastAPI application
   - Port: 8080
   - Location: Hetzner VPS `/opt/trading-bridge`
   - Process: `uvicorn app.main:app --host 0.0.0.0 --port 8080`

2. **Database** (PostgreSQL)
   - Provider: Railway
   - Connection: `DATABASE_URL` env variable
   - Tables: `bots`, `clients`, `trade_logs`, `exchange_credentials`, etc.

3. **Bot Runner Service** (`app/bot_runner.py`)
   - Background service managing bot lifecycle
   - Runs spread bots and volume bots
   - Auto-starts on app startup

4. **Exchange Connectors**
   - `app/coinstore_connector.py` - Coinstore API wrapper
   - `app/coinstore_adapter.py` - CCXT-like interface
   - `app/services/exchange.py` - Exchange manager

---

## 🔄 System Flows

### **1. Bot Creation Flow**

```
User (Frontend)
  ↓ POST /bots/create
Backend API (bot_routes.py)
  ↓ Validates client, creates bot record
Database (bots table)
  ↓ INSERT bot with status='stopped'
Response → Frontend
```

**Key Files:**
- `app/bot_routes.py:76` - `create_bot()` endpoint
- `app/database.py:134` - `Bot` model

---

### **2. Bot Start Flow**

```
User clicks "Start" (Frontend)
  ↓ POST /bots/{id}/start
Backend API (bot_routes.py)
  ↓ Updates bot.status = 'running'
Database (bots table)
  ↓ UPDATE status
Bot Runner Service (bot_runner.py)
  ↓ Detects status change
  ↓ Starts bot loop (async task)
Bot executes trades
  ↓ Logs to trade_logs table
```

**Key Files:**
- `app/bot_routes.py:2600` - `start_bot()` endpoint
- `app/bot_runner.py:1251` - `_run_spread_bot()` method
- `app/bot_runner.py:700` - `_run_volume_bot()` method

---

### **3. Spread Bot Trading Flow**

```
Spread Bot Cycle (_run_cycle)
  ↓
1. Fetch last traded price (ticker API)
  ↓ GET /v1/market/tickers
2. Calculate bid/ask prices (±spread from mid)
  ↓ bid_price = mid * (1 - spread%)
  ↓ ask_price = mid * (1 + spread%)
3. Calculate quantities from $10 USDT
  ↓ bid_qty = $10 / bid_price
  ↓ ask_qty = $10 / ask_price
4. Cancel existing orders
  ↓ POST /api/v1/order/cancel
5. Place limit orders
  ↓ POST /trade/order/place (BUY)
  ↓ POST /trade/order/place (SELL)
6. Log order placements
  ↓ INSERT INTO trade_logs (side='buy_placed')
7. Monitor for fills (poll every 5s)
  ↓ GET /api/v1/order/openOrders
  ↓ If order not in open orders → filled
8. Log filled trades
  ↓ INSERT INTO trade_logs (side='buy')
9. Refresh stale orders (every 60s)
  ↓ Cancel and restart cycle
```

**Key Files:**
- `app/spread_bot.py:105` - `_run_cycle()` method
- `app/spread_bot.py:270` - `_place_order()` method
- `app/spread_bot.py:312` - `_log_trade()` method
- `app/spread_bot.py:340` - `_log_order_placement()` method

---

### **4. Volume Bot Trading Flow**

```
Volume Bot Cycle (execute_trade)
  ↓
1. Check daily volume target
  ↓ If reached → skip
2. Random interval (15-45 min)
  ↓ Sleep until next trade
3. Determine trade side (buy/sell)
  ↓ Random or alternating
4. Execute market order
  ↓ POST /trade/order/place (MARKET)
5. Log trade
  ↓ INSERT INTO trade_logs
6. Update bot stats
  ↓ last_trade_time, health_status
```

**Key Files:**
- `app/cex_volume_bot.py:589` - `execute_trade()` method
- `app/cex_bot_runner.py:426` - Trade logging

---

### **5. Balance Fetch Flow**

```
Frontend requests balance
  ↓ GET /bots/{id}/balance-and-volume
Backend API (bot_routes.py)
  ↓
Exchange Adapter (coinstore_adapter.py)
  ↓ fetch_balance()
Coinstore Connector (coinstore_connector.py)
  ↓ get_balances()
  ↓ POST /spot/accountList
Coinstore API
  ↓ Returns balance data
Backend parses response
  ↓ Extracts SHARP/USDT balances
Response → Frontend
```

**Key Files:**
- `app/bot_routes.py:1525` - `get_bot_balance_and_volume()` endpoint
- `app/coinstore_adapter.py:124` - `fetch_balance()` method
- `app/coinstore_connector.py:270` - `get_balances()` method

---

## 🗄️ Database Schema

### **Core Tables**

#### **`bots` Table**
```sql
CREATE TABLE bots (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    account VARCHAR(255),              -- Links to clients.account_identifier
    connector VARCHAR(50),              -- 'coinstore', 'bitmart', etc.
    pair VARCHAR(20),                   -- 'SHARP/USDT'
    base_asset VARCHAR(20),             -- 'SHARP'
    quote_asset VARCHAR(20),             -- 'USDT'
    bot_type VARCHAR(20),                -- 'spread', 'volume'
    status VARCHAR(20),                  -- 'running', 'stopped'
    health_status VARCHAR(20),          -- 'healthy', 'stale', 'error'
    health_message TEXT,                -- Error/warning messages
    last_trade_time TIMESTAMP,
    last_heartbeat TIMESTAMP,
    status_updated_at TIMESTAMP,
    config JSONB,                       -- Bot configuration
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Key Relationships:**
- `bots.account` → `clients.account_identifier`
- `bots.id` → `trade_logs.bot_id`
- `bots.account` + `bots.connector` → `exchange_credentials` (via `clients.id`)

---

#### **`trade_logs` Table**
```sql
CREATE TABLE trade_logs (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) NOT NULL,
    side VARCHAR(10) NOT NULL,          -- 'buy', 'sell', 'buy_placed', 'sell_placed'
    amount DECIMAL(20, 8),              -- Trade amount
    price DECIMAL(20, 8),                -- Execution price
    cost_usd DECIMAL(20, 2),            -- Trade value in USD
    order_id VARCHAR(255),               -- Exchange order ID
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Usage:**
- **Spread Bot:** Logs `buy_placed`/`sell_placed` when orders placed, `buy`/`sell` when filled
- **Volume Bot:** Logs `buy`/`sell` when market orders execute
- **Frontend:** Reads from here for "Recent Activity"

---

#### **`exchange_credentials` Table**
```sql
CREATE TABLE exchange_credentials (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    exchange VARCHAR(50) NOT NULL,      -- 'coinstore', 'bitmart'
    api_key_encrypted TEXT NOT NULL,    -- Fernet encrypted
    api_secret_encrypted TEXT NOT NULL, -- Fernet encrypted
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, exchange)
);
```

**Encryption:**
- Uses `ENCRYPTION_KEY` environment variable
- Fernet symmetric encryption (`cryptography.fernet`)
- Decryption: `app/security.py:decrypt_credential()`

---

#### **`clients` Table**
```sql
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    account_identifier VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Links:**
- `clients.account_identifier` ← `bots.account`
- `clients.id` → `exchange_credentials.client_id`

---

## 🔌 API Endpoints

### **Bot Management**

| Endpoint | Method | Purpose | File |
|----------|--------|---------|------|
| `/bots` | GET | List all bots | `bot_routes.py:400` |
| `/bots/create` | POST | Create new bot | `bot_routes.py:76` |
| `/bots/{id}` | GET | Get bot details | `bot_routes.py:1300` |
| `/bots/{id}/start` | POST | Start bot | `bot_routes.py:2600` |
| `/bots/{id}/stop` | POST | Stop bot | `bot_routes.py:2700` |
| `/bots/{id}/balance-and-volume` | GET | Get balance & stats | `bot_routes.py:1525` |
| `/bots/{id}/trades` | GET | Get trade history | `bot_routes.py:1412` |
| `/bots/{id}/stats` | GET | Get bot statistics | `bot_routes.py:1994` |

### **Health & Status**

| Endpoint | Method | Purpose | File |
|----------|--------|---------|------|
| `/health` | GET | Main health check | `main.py:446` |
| `/health/bot-runner` | GET | Bot runner status | `main.py:517` |
| `/railway-ip` | GET | Get outbound IP | `main.py:487` |

---

## 📁 Code Organization

### **Directory Structure**

```
trading-bridge/
├── app/
│   ├── main.py                 # FastAPI app, routes, middleware
│   ├── database.py             # SQLAlchemy models, DB connection
│   ├── bot_routes.py           # Bot CRUD endpoints
│   ├── bot_runner.py          # Bot lifecycle management
│   ├── bot_health.py          # Health monitoring service
│   ├── spread_bot.py          # Spread bot logic
│   ├── cex_volume_bot.py      # Volume bot logic
│   ├── cex_bot_runner.py      # CEX bot execution
│   ├── coinstore_connector.py # Coinstore API wrapper
│   ├── coinstore_adapter.py   # CCXT-like interface
│   ├── security.py             # Encryption/decryption
│   └── services/
│       └── exchange.py        # Exchange manager
├── frontend/                   # Next.js frontend
├── migrations/                 # SQL migration files
└── .env                        # Environment variables
```

### **Key Modules**

#### **`app/main.py`**
- FastAPI application setup
- CORS configuration
- Rate limiting
- Bot runner startup/shutdown
- Health endpoints

#### **`app/bot_runner.py`**
- `BotRunner` class - manages bot lifecycle
- `_run_spread_bot()` - spread bot execution
- `_run_volume_bot()` - volume bot execution
- Auto-starts bots with `status='running'`

#### **`app/spread_bot.py`**
- `SpreadBot` class - spread bot implementation
- `_run_cycle()` - main trading cycle
- `_place_order()` - place limit orders
- `_log_trade()` - log filled trades
- `_log_order_placement()` - log order placements

#### **`app/coinstore_connector.py`**
- `CoinstoreConnector` class - low-level API wrapper
- `_request()` - HTTP request with signature
- `place_order()` - place orders (MARKET/LIMIT)
- `get_balances()` - fetch account balance
- Signature generation (HMAC-SHA256)

---

## ⚠️ Error Handling & Known Issues

### **Error Codes**

#### **Coinstore API Errors**

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| 1401 | Unauthorized | API key permissions or payload format | Check API key permissions, verify payload |
| 401 | signature-failed | Signature calculation error | Check JSON serialization, timestamp format |
| 200 | (with error code) | Application-level error | Check error message in response body |

**Known Issue: LIMIT Orders 1401**
- **Status:** ❌ BLOCKED
- **Symptom:** LIMIT orders return `1401 Unauthorized`, MARKET orders work
- **Location:** `app/coinstore_connector.py:358` (LIMIT order payload)
- **Attempted Fixes:**
  1. ✅ Removed `timestamp` from payload (didn't work)
  2. ✅ Added `timestamp` back (didn't work)
  3. ✅ Changed `ordPrice` to number type (didn't work)
  4. ✅ Changed `ordQty` to string with 2 decimals (didn't work)
  5. ✅ Verified precision (6 decimals price, 2 decimals quantity)
- **Current State:** Still failing, debug logging added
- **Document:** `SPREAD_BOT_LIMIT_ORDER_1401_HELP_REQUEST.md`

---

#### **Database Errors**

| Error | Cause | Fix |
|-------|-------|-----|
| `Database not available` | `DATABASE_URL` not set | Set `.env` file with `DATABASE_URL` |
| `relation "bots" does not exist` | Tables not created | Run migrations |
| `connection timeout` | Database unreachable | Check Railway status, network |

---

#### **Bot Errors**

| Error | Cause | Fix |
|-------|-------|-----|
| `Missing API keys` | No exchange credentials | Add via `/exchange-credentials` endpoint |
| `Balance fetch error: 1401` | API key permissions | Enable "Read" permission on API key |
| `Trade skipped - check balance` | Insufficient balance | Add funds to exchange account |

---

### **Known Limitations**

1. **Balance Checks Fail (1401)**
   - `/spot/accountList` returns 1401
   - Volume bot works by skipping balance check
   - Spread bot needs balance for order sizing (currently uses fixed $10)

2. **LIMIT Orders Not Working**
   - Spread bot cannot place LIMIT orders
   - Currently blocked on 1401 error
   - Workaround: Use MARKET orders (not ideal for spread bot)

3. **No Order Status Tracking**
   - Orders placed but status not persisted
   - Relies on exchange API for open orders check
   - If exchange API fails, orders may be "lost"

---

## 🚀 Deployment & Infrastructure

### **Production Environment**

**Backend:**
- **Server:** Hetzner VPS
- **IP:** 5.161.64.209
- **Port:** 8080
- **Process:** `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- **Location:** `/opt/trading-bridge`
- **Logs:** `/opt/trading-bridge/app.log`
- **Start Command:** `nohup uvicorn app.main:app --host 0.0.0.0 --port 8080 > app.log 2>&1 &`

**Database:**
- **Provider:** Railway PostgreSQL
- **Connection:** `DATABASE_URL` env variable
- **Location:** Railway dashboard → PostgreSQL service

**Frontend:**
- **Provider:** Railway/Vercel
- **URL:** https://app.pipelabs.xyz
- **Tech:** Next.js 16, React 19

---

### **Environment Variables**

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `ENCRYPTION_KEY` - Fernet encryption key (for API credentials)

**Optional:**
- `QUOTAGUARDSTATIC_URL` - Proxy URL for exchange APIs
- `DEBUG` - Debug mode (default: false)

**Location:** `/opt/trading-bridge/.env`

---

### **Restart Procedure**

```bash
# SSH into Hetzner
ssh root@5.161.64.209

# Navigate to app directory
cd /opt/trading-bridge

# Pull latest code
git pull origin main

# Kill existing process
pkill -f 'uvicorn app.main:app'

# Start app (with env vars loaded)
source venv/bin/activate
export $(cat .env | xargs)
nohup uvicorn app.main:app --host 0.0.0.0 --port 8080 > app.log 2>&1 &

# Verify it's running
ps aux | grep uvicorn
curl http://localhost:8080/health
```

---

## 🔧 Troubleshooting Guide

### **Bot Not Starting**

**Symptoms:**
- Bot status shows "stopped" after clicking start
- No logs in `app.log`

**Check:**
1. Bot runner service running? → `GET /health/bot-runner`
2. Database connection? → Check `DATABASE_URL` in `.env`
3. Bot record exists? → `SELECT * FROM bots WHERE id = '...'`
4. API keys configured? → `SELECT * FROM exchange_credentials WHERE client_id = ...`

**Fix:**
- Restart app: `pkill -f uvicorn && [restart command]`
- Check logs: `tail -f /opt/trading-bridge/app.log`

---

### **Balance Shows Zero**

**Symptoms:**
- Frontend shows "0 SHARP | 0 USDT"
- Bot has funds on exchange

**Check:**
1. Balance fetch working? → Check logs for `get_balances()` errors
2. API key permissions? → Must have "Read" permission
3. Currency names match? → Check `base_asset`/`quote_asset` in bot config

**Fix:**
- Enable "Read" permission on API key
- Verify currency names: `SHARP` vs `SHARPUSDT`

---

### **Orders Not Placing**

**Symptoms:**
- Bot running but no trades
- Error logs show 1401 or signature-failed

**Check:**
1. API key permissions? → Must have "Trade" permission
2. IP whitelisted? → Add Hetzner IP to exchange whitelist
3. Payload format? → Check debug logs for exact payload

**Fix:**
- Enable "Trade" permission
- Add IP to whitelist: `GET /railway-ip` (or Hetzner IP)
- Check `SPREAD_BOT_LIMIT_ORDER_1401_HELP_REQUEST.md` for LIMIT order issues

---

### **Recent Activity Not Showing**

**Symptoms:**
- Bot placing orders but frontend shows "No recent activity"

**Check:**
1. `trade_logs` table has entries? → `SELECT * FROM trade_logs WHERE bot_id = '...'`
2. Frontend fetching correctly? → Check browser network tab
3. Order placement logged? → Check `_log_order_placement()` calls

**Fix:**
- Verify `trade_logs` entries exist
- Check frontend API call: `GET /bots/{id}/trades`
- Ensure `_log_order_placement()` is called after order placement

---

## 📝 Change Log

### **2026-02-10**
- ✅ Added order placement logging for spread bot
- ✅ Updated spread bot defaults: 3% spread, 6 decimals price, 2 decimals quantity
- ✅ Added debug logging for LIMIT order payloads
- ⚠️ LIMIT orders still failing with 1401 (blocked)

### **2026-02-09**
- ✅ Fixed JSON serialization (removed `separators` parameter)
- ✅ Volume bot working with MARKET orders
- ⚠️ Balance checks failing with 1401 (workaround: skip balance check)

### **2026-02-08**
- ✅ Migrated from Railway to Hetzner VPS
- ✅ Set up PostgreSQL on Railway
- ✅ Configured exchange credentials encryption

---

## 🔗 Quick Reference

### **Important Files**

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app entry point |
| `app/bot_runner.py` | Bot lifecycle management |
| `app/spread_bot.py` | Spread bot implementation |
| `app/coinstore_connector.py` | Coinstore API wrapper |
| `app/bot_routes.py` | Bot API endpoints |
| `app/database.py` | Database models |

### **Important Endpoints**

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Check if app is running |
| `GET /health/bot-runner` | Check bot runner status |
| `GET /bots` | List all bots |
| `GET /bots/{id}/balance-and-volume` | Get bot balance |

### **Important Database Tables**

| Table | Purpose |
|-------|---------|
| `bots` | Bot configuration and status |
| `trade_logs` | Trade execution history |
| `exchange_credentials` | Encrypted API keys |
| `clients` | Client accounts |

### **Log Locations**

| Location | Purpose |
|----------|---------|
| `/opt/trading-bridge/app.log` | Application logs |
| Railway Dashboard → Logs | Database logs |
| Browser Console | Frontend errors |

---

## 📚 Additional Documentation

- `SPREAD_BOT_LIMIT_ORDER_1401_HELP_REQUEST.md` - LIMIT order 1401 error details
- `COINSTORE_SIGNATURE_BUG_REPORT.md` - Signature issues and fixes
- `TRADE_DATA_STORAGE_AND_ACCESS.md` - Trade logging details
- `PRODUCTION_READINESS_CHECKLIST.md` - Production checklist

---

**Last Updated:** February 10, 2026  
**Maintained By:** CTO / Development Team
