# 🚨 CRITICAL: Frontend Fix Required - Volume Bot API Keys

## Problem

**Clients are losing trust** - Volume bots show "Missing API keys" even though clients entered API keys during bot creation.

**Root Cause**: Frontend does NOT send `api_key`, `api_secret`, `passphrase` fields to backend when creating volume bots.

## Impact

- ❌ **1 client already lost**
- ❌ **Bots show "Missing API keys" error**
- ❌ **Balances show 0**
- ❌ **Clients can't see their funds**

## Files to Fix

**Primary File**: `ai-trading-ui/src/components/BotSetupWizard.jsx`

**Line**: Around line 665 (where `handleSubmit` calls `/clients/{client_id}/setup-bot`)

---

## Step-by-Step Fix

### Step 1: Find Where API Keys Are Collected

**Search for**: Where users enter API credentials in the wizard

**Look for**:
- Form inputs for "API Key", "API Secret", "Memo"
- State variables like `apiKey`, `apiSecret`, `memo`, `passphrase`
- Exchange credentials form section

**If API keys are NOT collected**, you need to add a form step first (see Step 3).

### Step 2: Locate the `handleSubmit` Function

**File**: `ai-trading-ui/src/components/BotSetupWizard.jsx`

**Find**: Function that creates the bot (around line 665)

**Current code likely looks like**:
```javascript
const handleSubmit = async () => {
  // ... validation code ...
  
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
      // ... config object ...
    }
    // ❌ MISSING: api_key, api_secret, passphrase
  };
  
  const botRes = await fetch(`${API_BASE}/clients/${clientIdToUse}/setup-bot`, {
    method: 'POST',
    headers,
    body: JSON.stringify(botPayload),
  });
  
  // ... handle response ...
};
```

### Step 3: Add API Key State (If Not Present)

**Add to component state** (near top of component):

```javascript
const [apiKey, setApiKey] = useState('');
const [apiSecret, setApiSecret] = useState('');
const [apiMemo, setApiMemo] = useState('');
```

### Step 4: Add API Key Form Fields (If Not Present)

**Add form fields in the exchange selection step**:

```javascript
{/* Add this in the exchange selection step */}
{isCEXExchange(selectedExchange) && (
  <div className="api-credentials-section" style={{ marginTop: '20px', padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
    <h3 style={{ marginBottom: '15px' }}>Exchange API Credentials</h3>
    <p style={{ color: '#666', marginBottom: '15px' }}>
      Enter your {selectedExchange} API credentials. These will be encrypted and stored securely.
    </p>
    
    <div style={{ marginBottom: '15px' }}>
      <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
        API Key <span style={{ color: 'red' }}>*</span>
      </label>
      <input
        type="text"
        value={apiKey}
        onChange={(e) => setApiKey(e.target.value)}
        placeholder={`Enter your ${selectedExchange} API Key`}
        required
        style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
      />
    </div>
    
    <div style={{ marginBottom: '15px' }}>
      <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
        API Secret <span style={{ color: 'red' }}>*</span>
      </label>
      <input
        type="password"
        value={apiSecret}
        onChange={(e) => setApiSecret(e.target.value)}
        placeholder={`Enter your ${selectedExchange} API Secret`}
        required
        style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
      />
    </div>
    
    {(selectedExchange === 'bitmart' || selectedExchange === 'coinstore') && (
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
          Memo/UID (Optional)
        </label>
        <input
          type="text"
          value={apiMemo}
          onChange={(e) => setApiMemo(e.target.value)}
          placeholder="Enter Memo/UID (for BitMart/Coinstore)"
          style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
        />
      </div>
    )}
  </div>
)}
```

**Add helper function**:

```javascript
const isCEXExchange = (exchange) => {
  if (!exchange) return false;
  const cexExchanges = [
    'bitmart', 'coinstore', 'binance', 'kucoin', 'gate', 'gateio', 
    'mexc', 'bybit', 'okx', 'kraken', 'coinbase', 'dydx', 
    'hyperliquid', 'htx', 'huobi', 'bitget', 'bitstamp', 'bitrue', 
    'bingx', 'btcmarkets', 'ndax', 'vertex', 'ascendex'
  ];
  return cexExchanges.includes(exchange.toLowerCase());
};
```

### Step 5: Update `handleSubmit` to Include API Keys

**Find the `handleSubmit` function** and update it:

```javascript
const handleSubmit = async () => {
  try {
    // ... existing validation code ...
    
    // ✅ ADD: Determine if this is a CEX bot
    const isCEX = isCEXExchange(selectedExchange);
    
    // ✅ ADD: Validate CEX bots have API keys
    if (isCEX) {
      if (!apiKey || !apiSecret) {
        alert('Please enter API Key and API Secret for CEX exchange bots');
        return;
      }
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
    
    // ✅ CRITICAL FIX: Add API credentials for CEX bots
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
    
    if (!botRes.ok) {
      const errorData = await botRes.json();
      throw new Error(errorData.detail || 'Failed to create bot');
    }
    
    const result = await botRes.json();
    
    // ... rest of existing success handling ...
    
  } catch (error) {
    console.error('Failed to create bot:', error);
    alert(`Failed to create bot: ${error.message}`);
    // ... existing error handling ...
  }
};
```

---

## Complete Example (Full Function)

Here's a complete example of what `handleSubmit` should look like:

```javascript
const handleSubmit = async () => {
  try {
    // Validation
    if (!selectedBotType) {
      alert('Please select a bot type');
      return;
    }
    
    if (!selectedExchange) {
      alert('Please select an exchange');
      return;
    }
    
    if (!baseAsset || !quoteAsset) {
      alert('Please enter base and quote assets');
      return;
    }
    
    // ✅ Determine if CEX bot
    const isCEX = isCEXExchange(selectedExchange);
    
    // ✅ Validate CEX bots have API keys
    if (isCEX && (!apiKey || !apiSecret)) {
      alert('Please enter API Key and API Secret for CEX exchange bots');
      return;
    }
    
    // Build config based on bot type
    let config = {};
    if (selectedBotType === 'volume') {
      config = {
        daily_volume_usd: dailyVolume || 5000,
        min_trade_usd: minTrade || 10,
        max_trade_usd: maxTrade || 25,
        interval_min_seconds: minInterval || 900,
        interval_max_seconds: maxInterval || 2700,
        slippage_bps: slippage || 50,
      };
    } else if (selectedBotType === 'spread') {
      config = {
        spread_bps: spreadBps || 50,
        order_size_usd: orderSize || 100,
        levels: levels || 3,
        refresh_seconds: refreshSeconds || 30,
        max_position_usd: maxPosition || 1000,
      };
    }
    
    // Build bot payload
    const botPayload = {
      name: botName || `${baseAsset} ${selectedBotType === 'volume' ? 'Volume' : 'Spread'} Bot`,
      bot_type: selectedBotType,
      exchange: selectedExchange,
      connector: selectedExchange,
      chain: selectedChain || (isCEX ? 'evm' : 'solana'),
      pair: `${baseAsset}/${quoteAsset}`,
      base_asset: baseAsset,
      quote_asset: quoteAsset,
      config: config,
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
    console.log('🚀 Creating bot with payload:', { ...botPayload, api_key: '***', api_secret: '***' });
    
    const botRes = await fetch(`${API_BASE}/clients/${clientIdToUse}/setup-bot`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Add any auth headers here
      },
      body: JSON.stringify(botPayload),
    });
    
    if (!botRes.ok) {
      const errorData = await botRes.json();
      throw new Error(errorData.detail || `HTTP ${botRes.status}: Failed to create bot`);
    }
    
    const result = await botRes.json();
    
    if (result.success) {
      console.log('✅ Bot created successfully:', result.bot_id);
      // Navigate to dashboard or show success message
      alert('Bot created successfully!');
      // ... navigate or refresh ...
    } else {
      throw new Error(result.message || 'Bot creation failed');
    }
    
  } catch (error) {
    console.error('❌ Failed to create bot:', error);
    alert(`Failed to create bot: ${error.message}`);
  }
};
```

---

## Testing Checklist

After implementing the fix:

1. ✅ **Create a new volume bot** with BitMart
   - Enter API Key, API Secret, Memo
   - Click "Create & Start Bot"
   - Should succeed without "Missing API keys" error

2. ✅ **Check backend logs** (Railway)
   - Should see: `💾 Saving API credentials for bitmart bot creation`
   - Should see: `✅ Saved API credentials for bitmart`

3. ✅ **Check database**
   ```sql
   SELECT client_id, exchange, updated_at 
   FROM exchange_credentials 
   WHERE client_id = 'your-client-id' AND exchange = 'bitmart';
   ```
   - Should return a row with recent `updated_at`

4. ✅ **Verify bot status**
   - Bot should NOT show "Missing API keys"
   - Bot should show balances (not 0)

5. ✅ **Test with Coinstore**
   - Same flow, should work

---

## Backend Status

✅ **Backend is READY** - Already accepts and saves API keys:
- Endpoint: `POST /clients/{client_id}/setup-bot`
- Model: `SetupBotRequest` includes `api_key`, `api_secret`, `passphrase`
- Logic: Saves credentials to `exchange_credentials` table if provided

---

## Urgency

🚨 **CRITICAL** - This must be fixed immediately:
- Clients are losing trust
- 1 client already left
- Production issue affecting all volume bot creations

---

## Quick Fix Summary

**What to change**:
1. Add `api_key`, `api_secret`, `passphrase` state variables
2. Add form fields to collect API credentials for CEX bots
3. Add API keys to `botPayload` before sending request

**Where**: `ai-trading-ui/src/components/BotSetupWizard.jsx` - `handleSubmit` function

**Time**: ~15-30 minutes to implement and test

---

## Need Help?

If you need help locating the exact code or have questions:
1. Search for `handleSubmit` in `BotSetupWizard.jsx`
2. Search for `setup-bot` endpoint call
3. Look for where `botPayload` is created

The fix is straightforward - just add the API key fields to the payload!
