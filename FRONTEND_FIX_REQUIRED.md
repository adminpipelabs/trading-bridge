# CRITICAL: Frontend Fix Required for Volume Bot API Keys

## Problem

**Clients are losing trust because volume bots show "Missing API keys" even though they entered API keys during bot creation.**

**Root Cause**: Frontend (`ai-trading-ui`) does NOT send `api_key`, `api_secret`, `passphrase` fields when creating volume bots.

## Current Frontend Flow (BROKEN)

**File**: `ai-trading-ui/src/components/BotSetupWizard.jsx` (around line 665)

**Current Code**:
```javascript
const botPayload = {
  name: "SHARP Volume Bot",
  bot_type: "volume",
  exchange: "bitmart",
  connector: "bitmart",
  chain: "evm",
  pair: "SHARP/USDT",
  base_asset: "SHARP",
  quote_asset: "USDT",
  config: {
    daily_volume_usd: 5000,
    min_trade_usd: 10,
    max_trade_usd: 25,
    // ... other config
  }
  // ❌ MISSING: api_key, api_secret, passphrase
};

const botRes = await fetch(`${API_BASE}/clients/${clientIdToUse}/setup-bot`, {
  method: 'POST',
  headers,
  body: JSON.stringify(botPayload),
});
```

## Required Fix

**File**: `ai-trading-ui/src/components/BotSetupWizard.jsx`

### Step 1: Find Where API Keys Are Collected

Look for where the user enters API credentials in the wizard. This is likely in:
- Step 2 (Exchange Selection)
- A separate API credentials form
- Or stored in component state

### Step 2: Add API Keys to botPayload

**Find the `handleSubmit` function** (around line 665) and update it:

```javascript
const handleSubmit = async () => {
  // ... existing code ...
  
  // Build bot payload
  const botPayload = {
    name: botName,
    bot_type: selectedBotType,
    exchange: selectedExchange,
    connector: selectedExchange,
    chain: selectedChain,
    pair: `${baseAsset}/${quoteAsset}`,
    base_asset: baseAsset,
    quote_asset: quoteAsset,
    config: {
      // ... existing config ...
    },
    // ✅ ADD THESE FIELDS FOR CEX BOTS:
    ...(isCEXBot && {
      api_key: apiKeyInput,        // From form state
      api_secret: apiSecretInput,  // From form state
      passphrase: memoInput || null // Optional, for BitMart
    })
  };
  
  // ... rest of submit logic ...
};
```

### Step 3: Ensure API Key Fields Are Collected

**If API keys are NOT collected in the wizard**, add a form step:

```javascript
// In BotSetupWizard.jsx, add state for API credentials:
const [apiKey, setApiKey] = useState('');
const [apiSecret, setApiSecret] = useState('');
const [apiMemo, setApiMemo] = useState('');

// Add form fields in the exchange selection step:
{isCEXBot && (
  <div className="api-credentials-form">
    <h3>Exchange API Credentials</h3>
    <input
      type="text"
      placeholder="API Key"
      value={apiKey}
      onChange={(e) => setApiKey(e.target.value)}
      required={isCEXBot}
    />
    <input
      type="password"
      placeholder="API Secret"
      value={apiSecret}
      onChange={(e) => setApiSecret(e.target.value)}
      required={isCEXBot}
    />
    {selectedExchange === 'bitmart' && (
      <input
        type="text"
        placeholder="Memo/UID (for BitMart)"
        value={apiMemo}
        onChange={(e) => setApiMemo(e.target.value)}
      />
    )}
  </div>
)}
```

### Step 4: Determine if Bot is CEX

```javascript
// Helper function to determine if bot is CEX
const isCEXBot = () => {
  const cexExchanges = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gate', 'gateio', 
                       'mexc', 'bybit', 'okx', 'kraken', 'coinbase'];
  return cexExchanges.includes(selectedExchange?.toLowerCase());
};
```

## Complete Example Fix

```javascript
// In BotSetupWizard.jsx

// Add state (if not already present)
const [apiKey, setApiKey] = useState('');
const [apiSecret, setApiSecret] = useState('');
const [apiMemo, setApiMemo] = useState('');

// In handleSubmit function (around line 665):
const handleSubmit = async () => {
  try {
    // Determine if this is a CEX bot
    const cexExchanges = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gate', 'gateio', 
                         'mexc', 'bybit', 'okx', 'kraken', 'coinbase'];
    const isCEX = cexExchanges.includes(selectedExchange?.toLowerCase());
    
    // Validate CEX bot has API keys
    if (isCEX && (!apiKey || !apiSecret)) {
      alert('Please enter API Key and API Secret for CEX bots');
      return;
    }
    
    // Build bot payload
    const botPayload = {
      name: botName || `${baseAsset} ${selectedBotType === 'volume' ? 'Volume' : 'Spread'} Bot`,
      bot_type: selectedBotType,
      exchange: selectedExchange,
      connector: selectedExchange,
      chain: selectedChain,
      pair: `${baseAsset}/${quoteAsset}`,
      base_asset: baseAsset,
      quote_asset: quoteAsset,
      config: {
        // ... existing config based on bot_type ...
      }
    };
    
    // ✅ CRITICAL: Add API credentials for CEX bots
    if (isCEX) {
      botPayload.api_key = apiKey;
      botPayload.api_secret = apiSecret;
      if (apiMemo) {
        botPayload.passphrase = apiMemo;
      }
    }
    
    // Send request
    const botRes = await fetch(`${API_BASE}/clients/${clientIdToUse}/setup-bot`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // ... existing headers ...
      },
      body: JSON.stringify(botPayload),
    });
    
    // ... rest of existing code ...
  } catch (error) {
    console.error('Failed to create bot:', error);
    // ... error handling ...
  }
};
```

## Testing Checklist

After implementing the fix:

1. ✅ **Create a new volume bot** with API keys
2. ✅ **Check backend logs** - should see: `💾 Saving API credentials for {exchange} bot creation`
3. ✅ **Check database** - credentials should be in `exchange_credentials` table
4. ✅ **Verify bot status** - should NOT show "Missing API keys"
5. ✅ **Check balance** - bot should show balances, not 0

## Backend Status

✅ **Backend is READY** - Already accepts and saves `api_key`, `api_secret`, `passphrase` fields
✅ **Endpoint**: `POST /clients/{client_id}/setup-bot` 
✅ **Model**: `SetupBotRequest` includes optional `api_key`, `api_secret`, `passphrase`

## Urgency

🚨 **CRITICAL** - Clients are losing trust. One client already left. This must be fixed immediately.

## Next Steps

1. **Locate** `ai-trading-ui` repository
2. **Open** `src/components/BotSetupWizard.jsx`
3. **Find** `handleSubmit` function (around line 665)
4. **Add** API key fields to `botPayload` for CEX bots
5. **Test** with a new volume bot creation
6. **Deploy** frontend changes

## Alternative: If Frontend Can't Be Updated Immediately

Use the backend endpoint to add credentials after bot creation:

```bash
POST /bots/{bot_id}/add-exchange-credentials?api_key=...&api_secret=...&passphrase=...
```

But this is a **workaround** - the proper fix is to update the frontend.
