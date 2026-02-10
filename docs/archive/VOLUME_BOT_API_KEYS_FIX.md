# Volume Bot API Keys Fix - Complete Solution

## Problem Summary

**Issue**: Volume bots show "Missing API keys - add connector or exchange credentials" even though API keys were entered when creating the bot.

**Root Cause**: 
1. The frontend doesn't send `api_key`/`api_secret` fields when creating bots via `/clients/{client_id}/setup-bot`
2. Existing bots created before the fix don't have credentials saved in `exchange_credentials` table

## What Was Fixed

### 1. Backend Now Accepts API Keys During Bot Creation ✅

**File**: `app/client_setup_routes.py`

- Added `api_key`, `api_secret`, `passphrase` fields to `SetupBotRequest` model
- Modified `/clients/{client_id}/setup-bot` endpoint to save API credentials if provided
- Credentials are encrypted and saved to `exchange_credentials` table

**How it works**:
- If `api_key` and `api_secret` are provided in the request → saves them automatically
- If not provided → checks if credentials already exist (backward compatibility)

### 2. New Endpoint to Fix Existing Bots ✅

**File**: `app/bot_routes.py`

**Endpoint**: `POST /bots/{bot_id}/add-exchange-credentials`

**Usage**:
```bash
curl -X POST "https://your-api.com/bots/{bot_id}/add-exchange-credentials?api_key=YOUR_KEY&api_secret=YOUR_SECRET&passphrase=YOUR_MEMO"
```

**What it does**:
- Adds exchange credentials for an existing bot
- Automatically detects exchange from bot name or connector
- Clears bot error status
- Saves credentials to `exchange_credentials` table

## For Existing Bots (Fix Now)

### Option 1: Use the New Endpoint (Recommended)

```bash
# Get bot ID from dashboard or database
BOT_ID="your-bot-id-here"
API_KEY="your-api-key"
API_SECRET="your-api-secret"
PASSPHRASE="your-memo"  # Optional, for BitMart

curl -X POST "https://your-api.com/bots/${BOT_ID}/add-exchange-credentials?api_key=${API_KEY}&api_secret=${API_SECRET}&passphrase=${PASSPHRASE}"
```

### Option 2: Use Existing Credentials Endpoint

```bash
# First, get client_id from bot
CLIENT_ID="your-client-id"
EXCHANGE="bitmart"  # or "coinstore"

curl -X POST "https://your-api.com/exchanges/credentials" \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: ${CLIENT_ID}" \
  -d '{
    "exchange": "'${EXCHANGE}'",
    "api_key": "your-api-key",
    "api_secret": "your-api-secret",
    "passphrase": "your-memo"
  }'
```

### Option 3: SQL Direct Insert (If API not working)

```sql
-- First, get client_id from bot
SELECT client_id, name, connector FROM bots WHERE id = 'your-bot-id';

-- Then insert credentials (replace values)
INSERT INTO exchange_credentials 
  (client_id, exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted, updated_at)
VALUES (
  'your-client-id',
  'bitmart',  -- or 'coinstore'
  encrypt('your-api-key'),  -- Note: You need to use the same encryption function
  encrypt('your-api-secret'),
  encrypt('your-memo'),
  NOW()
)
ON CONFLICT (client_id, exchange)
DO UPDATE SET 
  api_key_encrypted = EXCLUDED.api_key_encrypted,
  api_secret_encrypted = EXCLUDED.api_secret_encrypted,
  passphrase_encrypted = EXCLUDED.passphrase_encrypted,
  updated_at = NOW();
```

## For New Bots (Frontend Update Needed)

**Current Issue**: Frontend doesn't send `api_key`/`api_secret` when creating bots.

**Frontend Fix Required**:

Update `BotSetupWizard.jsx` to include API credentials in the request:

```javascript
const botPayload = {
  name: "SHARP Volume Bot",
  bot_type: "volume",
  exchange: "bitmart",
  connector: "bitmart",
  pair: "SHARP/USDT",
  base_asset: "SHARP",
  quote_asset: "USDT",
  config: { ... },
  // ADD THESE FIELDS:
  api_key: apiKeyInput,      // From form input
  api_secret: apiSecretInput, // From form input
  passphrase: memoInput      // Optional, for BitMart
};
```

## Verification

After adding credentials, check:

1. **Database**:
```sql
SELECT client_id, exchange, 
       LENGTH(api_key_encrypted) as key_length,
       LENGTH(api_secret_encrypted) as secret_length,
       updated_at
FROM exchange_credentials
WHERE client_id = 'your-client-id';
```

2. **Bot Status**: 
   - Bot error message should clear within 1-2 minutes
   - Check Railway logs for: `✅ Found API keys in exchange_credentials table`

3. **Balance**: 
   - Bot should now show balances instead of "Missing API keys"
   - Call `/bots/{bot_id}/balance-and-volume` to verify

## Next Steps

1. ✅ **Backend fix deployed** - New bots will save credentials if frontend sends them
2. ⏳ **Fix existing bots** - Use one of the options above
3. ⏳ **Update frontend** - Send `api_key`/`api_secret` when creating bots
4. ✅ **New endpoint available** - `/bots/{bot_id}/add-exchange-credentials` for fixing existing bots
