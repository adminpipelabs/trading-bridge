# Trade Data Storage & Access - For Reporting & AI Assistance

**Date:** February 10, 2026  
**Status:** ✅ Trade data is stored in `trade_logs` table

---

## 📊 **Data Storage Location**

### **Primary Table: `trade_logs`**

**Database:** Railway PostgreSQL  
**Table:** `trade_logs`  
**Purpose:** Stores all executed trades from CEX volume bots (market orders)

**Schema:**
```sql
CREATE TABLE trade_logs (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) NOT NULL,
    side VARCHAR(10) NOT NULL,           -- 'buy' or 'sell'
    amount DECIMAL(20, 8),              -- Trade amount in base asset
    price DECIMAL(20, 8),                -- Execution price
    cost_usd DECIMAL(20, 2),            -- Trade value in USD
    order_id VARCHAR(255),               -- Exchange order ID
    created_at TIMESTAMP DEFAULT NOW()   -- Trade timestamp
);

CREATE INDEX idx_trade_logs_bot ON trade_logs(bot_id, created_at DESC);
```

---

## 🔄 **Data Flow**

### **1. Trade Execution**
```
Volume Bot (cex_volume_bot.py)
  ↓ execute_trade() → Market order placed
  ↓ Returns: {side, amount, price, cost_usd, order_id}
  ↓
CEX Bot Runner (cex_bot_runner.py:426)
  ↓ INSERT INTO trade_logs
  ↓ Updates bots table (last_trade_time, health_status)
  ↓
PostgreSQL Database
  ↓ trade_logs table
```

### **2. Code Location**

**Trade Logging:** `app/cex_bot_runner.py` lines 424-432
```python
await conn.execute("""
    INSERT INTO trade_logs (bot_id, side, amount, price, cost_usd, order_id, created_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
""",
    bot_id, result["side"], result["amount"],
    result["price"], result["cost_usd"], result.get("order_id"),
    now_naive
)
```

---

## 🔌 **API Endpoints for Data Access**

### **1. Get Bot Trade History**
```
GET /bots/{bot_id}/trades-history
```
**Returns:**
```json
{
  "bot_id": "...",
  "bot_name": "...",
  "trades": [
    {
      "id": "123",
      "side": "buy",
      "amount": 1000.0,
      "price": 0.0015,
      "value_usd": 15.00,
      "order_id": "exchange_order_123",
      "status": "success",
      "created_at": "2026-02-10T07:30:00Z",
      "source": "trade_logs"
    }
  ],
  "total_volume": 150.00,
  "buy_count": 5,
  "sell_count": 3,
  "last_trade_time": "2026-02-10T07:30:00Z"
}
```

### **2. Get Paginated Trades**
```
GET /bots/{bot_id}/trades?limit=50
```
**Returns:** Same format as above, paginated

### **3. Get Balance & Volume (Includes Trade Data)**
```
GET /bots/{bot_id}/balance-and-volume
```
**Returns:**
```json
{
  "bot_id": "...",
  "balance": {
    "available": {...},
    "locked": {...},
    "volume_24h": 150.00,
    "trades_24h": {
      "buys": 5,
      "sells": 3
    }
  }
}
```

### **4. Get Client Trade History**
```
GET /api/clients/{client_id}/trade-history
```
**Returns:** All trades for all bots belonging to client

---

## 📈 **Direct Database Queries**

### **Get All Trades for Volume Bot**
```sql
SELECT 
    id,
    bot_id,
    side,
    amount,
    price,
    cost_usd,
    order_id,
    created_at
FROM trade_logs
WHERE bot_id = '{bot_id}'
ORDER BY created_at DESC;
```

### **Get Volume Statistics**
```sql
SELECT 
    bot_id,
    COUNT(*) as total_trades,
    SUM(CASE WHEN side = 'buy' THEN 1 ELSE 0 END) as buy_count,
    SUM(CASE WHEN side = 'sell' THEN 1 ELSE 0 END) as sell_count,
    SUM(cost_usd) as total_volume_usd,
    AVG(cost_usd) as avg_trade_size,
    MIN(created_at) as first_trade,
    MAX(created_at) as last_trade
FROM trade_logs
WHERE bot_id = '{bot_id}'
GROUP BY bot_id;
```

### **Get Daily Volume**
```sql
SELECT 
    DATE(created_at) as trade_date,
    COUNT(*) as trades,
    SUM(cost_usd) as daily_volume,
    SUM(CASE WHEN side = 'buy' THEN cost_usd ELSE 0 END) as buy_volume,
    SUM(CASE WHEN side = 'sell' THEN cost_usd ELSE 0 END) as sell_volume
FROM trade_logs
WHERE bot_id = '{bot_id}'
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY trade_date DESC;
```

### **Get Recent Trades (Last Hour)**
```sql
SELECT *
FROM trade_logs
WHERE bot_id = '{bot_id}'
  AND created_at >= NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

---

## 🤖 **For AI Assistance & Reporting**

### **Data Available:**
- ✅ Trade side (buy/sell)
- ✅ Trade amount (base asset)
- ✅ Execution price
- ✅ Trade value (USD)
- ✅ Exchange order ID
- ✅ Timestamp
- ✅ Bot ID (links to bot config)

### **What You Can Build:**
1. **Volume Reports** - Daily/weekly/monthly volume
2. **Trade Analysis** - Buy/sell ratios, trade frequency
3. **Performance Metrics** - Average trade size, execution patterns
4. **AI Insights** - Trade pattern recognition, optimization suggestions
5. **Real-time Monitoring** - Live trade feed, alerts

### **Example AI Query:**
```python
# Get trade patterns for AI analysis
trades = db.query("""
    SELECT side, amount, price, cost_usd, created_at
    FROM trade_logs
    WHERE bot_id = %s
    ORDER BY created_at DESC
    LIMIT 100
""", bot_id)

# Analyze:
# - Trade frequency
# - Buy/sell patterns
# - Volume trends
# - Optimal trade sizes
```

---

## 🔍 **Verify Data is Being Stored**

### **Check if trades exist:**
```sql
-- Find bot ID
SELECT id, name, status
FROM bots
WHERE name LIKE '%Volume Bot%Coinstore%';

-- Check trades (replace {bot_id})
SELECT COUNT(*) as trade_count, 
       SUM(cost_usd) as total_volume,
       MAX(created_at) as last_trade
FROM trade_logs
WHERE bot_id = '{bot_id}';
```

### **If no trades after 30 minutes:**
1. Check Hetzner logs for trade execution
2. Verify `trade_logs` table exists
3. Check bot runner is active
4. Verify bot is executing trades (not just waiting)

---

## 📋 **Summary**

**Data Location:** `trade_logs` table in Railway PostgreSQL  
**Data Flow:** Bot → Runner → Database → API → Reports/AI  
**Access Methods:**
- ✅ API endpoints (`/bots/{id}/trades-history`)
- ✅ Direct SQL queries
- ✅ Client-level endpoints (`/api/clients/{id}/trade-history`)

**For Reporting/AI:**
- All trade data is stored with timestamps
- Can query by bot, date range, side
- Includes USD values for easy aggregation
- Links to bot config via `bot_id`

**Next Step:** Verify trades are being logged by checking `trade_logs` table.
