# Bot "Error" Status - Explained

**Bot:** Volume Bot - Real Lynk  
**Platform:** Jupiter (Solana)  
**Status:** Error ⚠️

---

## 🔍 **What "Error" Status Means**

The bot health monitor detected a problem that prevents the bot from trading. The bot is **not running** and **will not execute trades** until the error is fixed.

---

## 📋 **How to Find the Exact Error**

### **Method 1: Check UI (Easiest)**

The error message should be displayed **next to the status badge** in the bot list. Look for:
- Small gray text next to the "⚠️ Error" badge
- **Hover over the status badge** - tooltip shows full error message

If you don't see it, the `health_message` might be empty (check Railway logs).

### **Method 2: Check Railway Logs**

1. Go to **Railway Dashboard** → **trading-bridge** → **Logs**
2. Search for: `Real Lynk` or `Lynk` or the bot ID
3. Look for:
   - `health_status='error'`
   - `health_message = '...'`
   - `No wallet address found`
   - `Bot missing pair configuration`
   - `Health check error`

### **Method 3: Check Database Directly**

Run this SQL query in Railway PostgreSQL:

```sql
SELECT 
    name,
    status,
    health_status,
    health_message,
    wallet_address,
    base_mint,
    quote_mint
FROM bots
WHERE name LIKE '%Real Lynk%' OR name LIKE '%Lynk%';
```

The `health_message` column contains the **exact error reason**.

---

## 🎯 **Common Error Messages & Fixes**

### **1. "No wallet address found for Solana bot"** ⚠️ MOST COMMON

**What it means:**
- Bot doesn't have a wallet address configured
- Private key wasn't saved or wallet wasn't derived

**Fix:**
1. **Edit the bot** → Re-add the private key
2. Or **re-create the bot** with proper wallet configuration

**Check:**
```sql
SELECT wallet_address FROM bots WHERE name LIKE '%Real Lynk%';
-- Should return a Solana address (base58, 32-44 chars)
```

---

### **2. "Bot missing pair configuration (no base_mint found)"**

**What it means:**
- Bot doesn't know which token to trade
- Token mint address (`base_mint`) is missing

**Fix:**
1. **Edit the bot** → Add token mint address
2. Or **re-create the bot** with proper token configuration

**Check:**
```sql
SELECT base_mint, config->>'base_mint' FROM bots WHERE name LIKE '%Real Lynk%';
-- Should return a token mint address
```

---

### **3. "Health check error: {details}"**

**What it means:**
- Health monitor tried to check the bot but failed
- Could be RPC connection, invalid addresses, etc.

**Common causes:**
- Invalid wallet address format
- Solana RPC connection timeout
- Token mint address doesn't exist
- Wallet has no SOL (can't pay fees)

**Fix:**
- Check Railway logs for specific error
- Verify wallet address is correct
- Ensure wallet has SOL for fees
- Check token mint address exists

---

### **4. "Failed to initialize Jupiter client/signer"**

**What it means:**
- Bot runner couldn't connect to Solana RPC
- Jupiter API might be down

**Fix:**
- Check `SOLANA_RPC_URL` environment variable
- Verify Solana RPC is accessible
- Check Railway logs for connection errors

---

### **5. "Bot crashed: {error}"**

**What it means:**
- Bot was running but encountered an exception
- Bot runner caught the error and stopped the bot

**Fix:**
- Check Railway logs for full stack trace
- Look for the specific error that caused the crash
- Common causes: Invalid config, API errors, network issues

---

## 🔧 **Quick Diagnostic Steps**

### **Step 1: Get Bot Details**

```sql
SELECT 
    id,
    name,
    status,
    health_status,
    health_message,
    wallet_address,
    base_mint,
    quote_mint,
    config
FROM bots
WHERE name LIKE '%Real Lynk%';
```

### **Step 2: Check Wallet**

```sql
SELECT 
    bw.bot_id,
    bw.wallet_address,
    tk.wallet_address as trading_key_address
FROM bot_wallets bw
LEFT JOIN bots b ON b.id = bw.bot_id
LEFT JOIN clients c ON c.account_identifier = b.account
LEFT JOIN trading_keys tk ON tk.client_id = c.id AND tk.chain = 'solana'
WHERE b.name LIKE '%Real Lynk%';
```

### **Step 3: Check Railway Logs**

Search for:
- `Real Lynk`
- `health_status='error'`
- `No wallet address`
- `missing pair configuration`
- `Health check error`

---

## ✅ **Most Likely Issue for Real Lynk**

Based on common patterns, **most likely causes:**

1. **Missing wallet address** (60% chance)
   - Bot was created but private key wasn't saved
   - Solution: Edit bot → Re-add private key

2. **Missing token configuration** (30% chance)
   - Bot doesn't have `base_mint` (token address)
   - Solution: Edit bot → Add token mint address

3. **Health check failure** (10% chance)
   - RPC connection issue or invalid addresses
   - Solution: Check Railway logs for specific error

---

## 🚀 **How to Fix**

1. **Find the exact error:**
   - Check UI for `health_message` (hover over status badge)
   - Or check Railway logs
   - Or run SQL query above

2. **Fix based on error:**
   - Missing wallet → Re-add private key
   - Missing token → Add token mint address
   - Health check error → Check logs for details

3. **Restart bot:**
   - After fixing, click "Start Bot"
   - Bot should initialize and start trading

---

## 📞 **If Still Stuck**

If you can't find the error message:
1. Check Railway logs → Search for bot name
2. Run SQL query → Check `health_message` column
3. Check browser console → Look for API errors

The `health_message` field **always** contains the exact reason why the bot is in error state!
