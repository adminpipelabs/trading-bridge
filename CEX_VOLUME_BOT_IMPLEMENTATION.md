# CEX Volume Bot Implementation - Complete ✅

## Overview

Reusable volume bot for centralized exchanges (BitMart, Coinstore, Binance, etc.) using ccxt. Same logic as Jupiter/Solana bot, adapted for CEX.

---

## Files Created

### 1. Database Migration
**File:** `migrations/add_cex_volume_bot.sql`
- Creates `exchange_credentials` table for encrypted API keys
- Adds `exchange`, `base_asset`, `quote_asset` columns to `bots` table
- Creates `trade_logs` table for trade history

### 2. Exchange Configurations
**File:** `app/cex_exchanges.py`
- Exchange-specific configs (BitMart, Coinstore, Binance, KuCoin)
- Fee structures, rate limits, minimums

### 3. Bot Logic
**File:** `app/cex_volume_bot.py`
- `CEXVolumeBot` class - main bot implementation
- Alternating buy/sell market orders
- Random trade sizes and intervals
- Daily volume tracking
- Position imbalance management
- Encrypted credential handling

### 4. Background Runner
**File:** `app/cex_bot_runner.py`
- `CEXBotRunner` class - manages all active CEX bots
- Runs every 10 seconds, checks for trades
- Auto-initializes new bots
- Updates database with trade results

### 5. API Routes
**File:** `app/cex_credential_routes.py`
- `POST /exchanges/credentials` - Add/update exchange credentials
- `GET /exchanges/credentials` - List connected exchanges
- `DELETE /exchanges/credentials/{exchange}` - Remove credentials
- `POST /exchanges/admin/{client_id}/credentials` - Admin add credentials

### 6. Integration
**Updated:** `app/main.py`
- Added CEX bot runner to lifespan
- Registered credential routes
- Proper startup/shutdown handling

**Updated:** `app/bot_routes.py`
- Updated `start_bot` to handle CEX bots
- CEX bots auto-start via runner (no manual start needed)

---

## Database Migration

**Run this SQL in Railway PostgreSQL:**

```sql
-- See migrations/add_cex_volume_bot.sql for full migration
```

Or run the file directly:
```bash
psql $DATABASE_URL < migrations/add_cex_volume_bot.sql
```

---

## Usage

### 1. Add Exchange Credentials (Admin)

```bash
curl -X POST https://trading-bridge-production.up.railway.app/exchanges/admin/{client_id}/credentials \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "exchange": "bitmart",
    "api_key": "...",
    "api_secret": "..."
  }'
```

### 2. Create CEX Volume Bot

```bash
curl -X POST https://trading-bridge-production.up.railway.app/bots \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sharp BitMart Volume",
    "account": "client_sharp",
    "bot_type": "volume",
    "exchange": "bitmart",
    "base_asset": "SHARP",
    "quote_asset": "USDT",
    "connector": "bitmart",
    "pair": "SHARP-USDT",
    "strategy": "volume",
    "config": {
      "daily_volume_usd": 10000,
      "min_trade_usd": 20,
      "max_trade_usd": 50,
      "interval_min_seconds": 600,
      "interval_max_seconds": 1800
    }
  }'
```

### 3. Start Bot

```bash
curl -X POST https://trading-bridge-production.up.railway.app/bots/{bot_id}/start
```

The CEX bot runner will automatically:
- Detect the bot is running
- Load credentials from `exchange_credentials` table
- Initialize exchange connection
- Start executing trades based on intervals

---

## Features

✅ **Reusable** - Works with any ccxt exchange (BitMart, Coinstore, Binance, KuCoin, etc.)  
✅ **Same pattern** as Jupiter bot - alternating buys/sells, random sizes/intervals  
✅ **Encrypted credentials** - Same security model as wallet keys  
✅ **Background runner** - Checks every 10 seconds, executes when interval elapsed  
✅ **Trade logging** - Full history in `trade_logs` table  
✅ **Proxy support** - Automatically uses QuotaGuard static IP if configured  
✅ **Daily volume tracking** - Stops when target reached  
✅ **Position balancing** - Prevents excessive imbalance  

---

## Configuration

### Bot Config (in `config` JSON field):

```json
{
  "daily_volume_usd": 10000,      // Daily target in USD
  "min_trade_usd": 20,             // Minimum trade size
  "max_trade_usd": 50,              // Maximum trade size
  "interval_min_seconds": 600,      // Min seconds between trades
  "interval_max_seconds": 1800,     // Max seconds between trades
  "max_position_imbalance": 0.2    // Max 20% imbalance before forcing opposite side
}
```

### Supported Exchanges:

- **BitMart** - ✅ Ready (no passphrase)
- **Coinstore** - ✅ Ready (no passphrase)
- **Binance** - ✅ Ready (no passphrase, has testnet)
- **KuCoin** - ✅ Ready (requires passphrase)

---

## How It Works

1. **Bot Created** → Status set to 'running'
2. **CEX Runner** → Detects bot every 10 seconds
3. **Load Credentials** → Decrypts from `exchange_credentials` table
4. **Initialize Exchange** → Creates ccxt instance with proxy if configured
5. **Check Interval** → If enough time elapsed since last trade
6. **Execute Trade** → Random buy/sell market order
7. **Update Database** → Log trade, update health status
8. **Repeat** → Until daily target reached or bot stopped

---

## Next Steps

1. **Run Database Migration** - Execute `migrations/add_cex_volume_bot.sql`
2. **Add BitMart Credentials** - Use admin endpoint for Real Sharp client
3. **Create Bot** - Via bot creation endpoint with exchange="bitmart"
4. **Start Bot** - Bot will auto-start via CEX runner
5. **Monitor** - Check logs and `trade_logs` table

---

## Testing

After deployment, check:
- ✅ CEX bot runner starts in logs
- ✅ Credentials can be added via API
- ✅ Bot can be created with exchange field
- ✅ Bot starts and executes trades
- ✅ Trades appear in `trade_logs` table

---

## Notes

- **Proxy Support**: Automatically uses `QUOTAGUARD_PROXY_URL` if set
- **Encryption**: Uses same `ENCRYPTION_KEY` as wallet keys
- **Error Handling**: Failed bots marked as 'error' in health_status
- **Daily Reset**: Volume counter resets at midnight UTC
- **Balance Checks**: Skips trades if insufficient balance

---

**Status:** ✅ **IMPLEMENTATION COMPLETE**

Ready for Real Sharp BitMart volume bot! 🚀
