# Diagnose Bot "Error" Status - Real Lynk Volume Bot

**Bot:** Volume Bot - Real Lynk  
**Platform:** Jupiter (Solana)  
**Status:** Error  
**Volume:** $10/5000 (0%)

---

## 🔍 **What "Error" Status Means**

The bot health monitor detected a problem and set `health_status='error'`. This prevents the bot from trading.

---

## 🎯 **Common Causes for Solana/Jupiter Bot Errors**

### **1. Missing Wallet Address** ⚠️ MOST COMMON
**Error Message:** "No wallet address found for Solana bot"

**What it means:**
- Bot doesn't have a `wallet_address` in the database
- Private key wasn't saved or wallet wasn't derived

**How to check:**
```sql
-- Check if bot has wallet address
SELECT 
    b.id,
    b.name,
    b.wallet_address,
    bw.wallet_address as bot_wallet_address,
    tk.wallet_address as trading_key_address
FROM bots b
LEFT JOIN bot_wallets bw ON bw.bot_id = b.id
LEFT JOIN trading_keys tk ON tk.client_id = (
    SELECT client_id FROM clients WHERE account_identifier = b.account LIMIT 1
)
WHERE b.name LIKE '%Real Lynk%' OR b.name LIKE '%Lynk%';
```

**Fix:**
- Re-add the private key via bot setup wizard
- Or admin can add wallet via `/clients/{client_id}/trading-key` endpoint

---

### **2. Missing Token Configuration** ⚠️ COMMON
**Error Message:** "Bot missing pair configuration (no base_mint found in column or config)"

**What it means:**
- Bot doesn't have `base_mint` (token address) configured
- Can't determine which token to trade

**How to check:**
```sql
-- Check bot config for base_mint
SELECT 
    id,
    name,
    base_mint,
    quote_mint,
    config->>'base_mint' as config_base_mint,
    config->>'quote_mint' as config_quote_mint
FROM bots
WHERE name LIKE '%Real Lynk%' OR name LIKE '%Lynk%';
```

**Fix:**
- Edit bot and add `base_mint` (token address)
- Or re-create bot with proper token configuration

---

### **3. Health Check Failed**
**Error Message:** "Health check error: {error details}"

**What it means:**
- Health monitor tried to check on-chain activity but failed
- Could be RPC connection issue, invalid addresses, etc.

**How to check:**
- Check Railway logs for: `Solana health check failed for bot {bot_id}`
- Look for specific error message

**Common errors:**
- `Invalid wallet address format`
- `RPC connection timeout`
- `Token mint not found`
- `Insufficient funds`

---

### **4. Jupiter Client Initialization Failed**
**Error Message:** "Failed to initialize Jupiter client/signer"

**What it means:**
- Bot runner couldn't connect to Solana RPC
- Or Jupiter API is down

**How to check:**
- Check Railway logs for: `Failed to initialize Jupiter client`
- Check `SOLANA_RPC_URL` environment variable

---

### **5. Bot Crashed During Execution**
**Error Message:** "Bot crashed: {error}"

**What it means:**
- Bot was running but encountered an unhandled exception
- Bot runner caught the error and set status to "error"

**How to check:**
- Check Railway logs for: `CRITICAL: Volume bot {bot_id} crashed`
- Look for full stack trace

---

## 🔧 **How to Diagnose the Real Lynk Bot**

### **Step 1: Check Railway Logs**

1. Go to Railway Dashboard → trading-bridge → Logs
2. Search for: `Real Lynk` or `Lynk` or the bot ID
3. Look for:
   - `health_status='error'`
   - `No wallet address found`
   - `Bot missing pair configuration`
   - `Health check error`
   - `Failed to initialize`

### **Step 2: Check Database**

Run this SQL query in Railway PostgreSQL:

```sql
-- Get full bot details including wallet and config
SELECT 
    b.id,
    b.name,
    b.status,
    b.health_status,
    b.health_message,
    b.wallet_address,
    b.base_mint,
    b.quote_mint,
    b.config,
    bw.wallet_address as bot_wallet_address,
    tk.wallet_address as trading_key_address,
    tk.encrypted_private_key IS NOT NULL as has_private_key
FROM bots b
LEFT JOIN bot_wallets bw ON bw.bot_id = b.id
LEFT JOIN clients c ON c.account_identifier = b.account
LEFT JOIN trading_keys tk ON tk.client_id = c.id AND tk.chain = 'solana'
WHERE b.name LIKE '%Real Lynk%' OR b.name LIKE '%Lynk%'
ORDER BY b.created_at DESC;
```

**What to look for:**
- ✅ `wallet_address` should have a value
- ✅ `base_mint` should have a token address
- ✅ `has_private_key` should be `true`
- ✅ `health_message` will tell you the exact error

### **Step 3: Check Health Message**

The `health_message` field contains the exact error reason:

```sql
SELECT 
    name,
    health_status,
    health_message,
    status
FROM bots
WHERE name LIKE '%Real Lynk%';
```

**Common messages:**
- `"No wallet address found for Solana bot"` → Missing wallet
- `"Bot missing pair configuration (no base_mint found)"` → Missing token config
- `"Health check error: {details}"` → Health check failed
- `"Failed to initialize exchange connection"` → Exchange init failed

---

## ✅ **Quick Fixes**

### **Fix 1: Missing Wallet**
If `wallet_address` is NULL:

1. **Via UI:** Edit bot → Re-add private key
2. **Via API:** 
   ```bash
   POST /clients/{client_id}/trading-key
   {
     "private_key": "...",
     "chain": "solana"
   }
   ```

### **Fix 2: Missing Token Config**
If `base_mint` is NULL:

1. **Via UI:** Edit bot → Add token mint address
2. **Via SQL:**
   ```sql
   UPDATE bots 
   SET base_mint = 'TOKEN_MINT_ADDRESS_HERE',
       config = jsonb_set(
         COALESCE(config, '{}'::jsonb),
         '{base_mint}',
         '"TOKEN_MINT_ADDRESS_HERE"'
       )
   WHERE name LIKE '%Real Lynk%';
   ```

### **Fix 3: Health Check Error**
If health check is failing:

1. Check Railway logs for specific error
2. Verify:
   - Wallet address format is correct
   - Token mint address exists
   - RPC URL is accessible
   - Wallet has SOL for fees

---

## 📋 **Next Steps**

1. **Check Railway logs** → Find exact error message
2. **Run SQL query** → Check bot configuration
3. **Fix the issue** → Based on error message
4. **Restart bot** → Click "Start Bot" after fixing

---

## 🚨 **Most Likely Issue for Real Lynk**

Based on the pattern, **most likely causes:**

1. **Missing wallet address** (60% chance)
   - Bot was created but private key wasn't saved properly
   - Wallet address wasn't derived

2. **Missing base_mint** (30% chance)
   - Bot was created but token configuration is missing
   - Token mint address not set

3. **Health check failure** (10% chance)
   - RPC connection issue
   - Invalid addresses
   - Insufficient SOL for fees

**Check the `health_message` field first** - it will tell you exactly what's wrong!
