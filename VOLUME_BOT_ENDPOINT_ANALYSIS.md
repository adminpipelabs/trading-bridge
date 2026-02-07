# Volume Bot Endpoint Analysis - Answers to Dev Questions

## Question 1: What endpoint does Volume Bot wizard call?

**Answer**: `/clients/{client_id}/setup-bot` (POST)

**Location**: `ai-trading-ui/src/components/BotSetupWizard.jsx` line 665

```javascript
const botRes = await fetch(`${API_BASE}/clients/${clientIdToUse}/setup-bot`, {
  method: 'POST',
  headers,
  body: JSON.stringify(botPayload),
});
```

**Payload for Volume Bot**:
```json
{
  "name": "SHARP Volume Bot",
  "bot_type": "volume",  // ← Key field
  "exchange": "bitmart",
  "connector": "bitmart",
  "chain": "evm",
  "pair": "SHARP/USDT",
  "base_asset": "SHARP",
  "quote_asset": "USDT",
  "base_mint": null,
  "private_key": null,  // CEX bots don't need private key
  "config": {
    "daily_volume_usd": 5000,
    "min_trade_usd": 10,
    "max_trade_usd": 25,
    "interval_min_seconds": 900,
    "interval_max_seconds": 2700,
    "slippage_bps": 50
  }
}
```

---

## Question 2: What endpoint does Spread Bot wizard call?

**Answer**: `/clients/{client_id}/setup-bot` (POST) - **SAME ENDPOINT**

**Location**: `ai-trading-ui/src/components/BotSetupWizard.jsx` line 665 (same code path)

**Payload for Spread Bot**:
```json
{
  "name": "SHARP Spread Bot",
  "bot_type": "spread",  // ← Key field
  "exchange": "bitmart",
  "connector": "bitmart",
  "chain": "evm",
  "pair": "SHARP/USDT",
  "base_asset": "SHARP",
  "quote_asset": "USDT",
  "base_mint": null,
  "private_key": null,
  "config": {
    "spread_bps": 50,
    "order_size_usd": 100,
    "levels": 3,
    "refresh_seconds": 30,
    "max_position_usd": 1000
  }
}
```

---

## Question 3: Are they the same or different?

**Answer**: **SAME ENDPOINT** ✅

Both volume and spread bots use:
- **Same endpoint**: `POST /clients/{client_id}/setup-bot`
- **Same backend handler**: `app/client_setup_routes.py` - `setup_bot()` function
- **Same validation**: `if request.bot_type not in BOT_TYPE_CONFIGS`

---

## Bot Type Validation Check

**Backend validation** (`app/client_setup_routes.py` line 357):
```python
# Validate bot type
if request.bot_type not in BOT_TYPE_CONFIGS:
    raise HTTPException(status_code=400, detail=f"Invalid bot_type. Must be one of: {list(BOT_TYPE_CONFIGS.keys())}")
```

**BOT_TYPE_CONFIGS** (line 272):
```python
BOT_TYPE_CONFIGS = {
    "volume": {
        "label": "Volume Bot",
        "description": "Generates trading volume with randomized buy/sell orders over time.",
        "chain": "solana",  # ← Default chain
        "default_config": {
            "daily_volume_usd": 5000,
            "min_trade_usd": 10,
            "max_trade_usd": 25,
            "interval_min_seconds": 900,
            "interval_max_seconds": 2700,
            "slippage_bps": 50,
        }
    },
    "spread": {
        "label": "Spread Bot",
        "description": "Market making bot that places bid/ask orders around the current price.",
        "chain": "evm",  # ← Default chain
        "default_config": {
            "bid_spread": 0.3,
            "ask_spread": 0.3,
            "order_amount": 1600,
        }
    }
}
```

**✅ Validation allows both "volume" and "spread"** - no issue here.

---

## Potential Issue Found

**CEX Bot Config Handling** (line 541-543):
```python
else:
    # CEX bots - use config as-is
    merged_config = config_dict
```

**DEX Bot Config Handling** (line 533-540):
```python
if not is_cex:
    bot_config = BOT_TYPE_CONFIGS[request.bot_type]
    merged_config = {**bot_config["default_config"], **config_dict}
    
    # For Solana bots, only set quote_mint to SOL if not provided (native token)
    if chain == "solana" and request.bot_type == "volume":
        if "quote_mint" not in merged_config:
            merged_config["quote_mint"] = "So11111111111111111111111111111111111111112"  # SOL
```

**Observation**: 
- DEX bots merge defaults from `BOT_TYPE_CONFIGS`
- CEX bots use config as-is (no defaults merged)
- This shouldn't cause creation failure, but might affect bot behavior

---

## What to Check Next

### 1. Railway Backend Logs
When volume bot is created, check for:
```
🟢 CLIENT SETUP: Creating bot via /clients/{id}/setup-bot
   Bot: name=..., bot_type=volume, exchange=bitmart, is_cex=True
   After save: bot.account=..., bot.bot_type=volume
✅ Bot setup completed successfully
```

**OR** errors:
```
❌ Unexpected error in setup_bot
⚠️ WARNING: Bot bot_type mismatch
Failed to set up bot: ...
```

### 2. Browser Network Tab
Check the actual request/response:
- **Request URL**: Should be `/clients/{client_id}/setup-bot`
- **Request Payload**: Should have `"bot_type": "volume"`
- **Response Status**: Should be 200 OK
- **Response Body**: Should have `{"success": true, "bot_id": "..."}`

### 3. Database Transaction
Check if transaction is rolled back:
```sql
-- Check for bots created around the same time
SELECT id, name, bot_type, account, client_id, status, created_at, error
FROM bots 
WHERE client_id = '7142fefa-3aaf-4883-a649-74738e4866dd'
ORDER BY created_at DESC;
```

---

## Quick Test: Manual SQL Insert

As suggested by dev, try manually inserting a volume bot:

```sql
INSERT INTO bots (
    id, 
    client_id,
    account, 
    instance_name,
    name, 
    bot_type, 
    connector,
    exchange,
    pair,
    base_asset,
    quote_asset,
    strategy,
    status, 
    config, 
    stats,
    health_status,
    created_at,
    updated_at
)
VALUES (
    gen_random_uuid(),
    '7142fefa-3aaf-4883-a649-74738e4866dd',  -- Same client_id as spread bot
    'client_new_sharp_foundation',  -- Same account as spread bot
    'client_new_sharp_foundation_' || substr(gen_random_uuid()::text, 1, 8),
    'Sharp-VB-BitMart',  -- Volume Bot
    'volume',  -- ← Key: bot_type = volume
    'bitmart',
    'bitmart',
    'SHARP/USDT',
    'SHARP',
    'USDT',
    'volume',  -- strategy matches bot_type
    'created',
    '{"daily_volume_usd": 5000, "min_trade_usd": 10, "max_trade_usd": 25, "interval_min_seconds": 900, "interval_max_seconds": 2700, "slippage_bps": 50}'::jsonb,
    '{}'::jsonb,
    'unknown',
    NOW(),
    NOW()
);
```

**If this works and shows in UI** → Database/UI are fine, problem is in backend creation logic.

**If this doesn't show in UI** → Problem is in UI query/filtering.

---

## Summary

✅ **Same endpoint** for both volume and spread bots  
✅ **Validation allows both** bot types  
❓ **Need to check**: Railway logs to see why volume bot creation fails  
❓ **Need to test**: Manual SQL insert to isolate the issue
