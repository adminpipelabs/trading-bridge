# Uniswap Connector - Phase 4 Testing Guide

## ✅ Pre-Testing Checklist

### 1. Wallet Funding

**Test Wallet Requirements:**
- **POL:** ~1 POL (~$0.50) for gas fees
- **USDC:** $50 for trades
- **SHARP:** Can buy with first trade or fund separately

**Funding Steps:**
1. Send POL to test wallet address (for gas)
2. Send USDC to test wallet address
3. Optionally send SHARP, or let bot buy on first trade

### 2. Bot Configuration

**Create EVM Volume Bot via UI:**

```json
{
  "name": "SHARP Polygon Test",
  "bot_type": "volume",
  "chain": "polygon",
  "base_token": "0xb36b62929762acf8a9cc27ecebf6d353ebb48244",
  "quote_token": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
  "daily_volume_usd": 100,
  "min_trade_usd": 5,
  "max_trade_usd": 10,
  "interval_min_seconds": 300,
  "interval_max_seconds": 600,
  "slippage_bps": 50
}
```

**Field Mapping:**
- `chain`: "polygon" (required for EVM bot)
- `base_token`: SHARP contract address
- `quote_token`: USDC contract address (defaults to chain USDC if not specified)
- `daily_volume_usd`: Target volume per day
- `min_trade_usd` / `max_trade_usd`: Trade size range
- `interval_min_seconds` / `interval_max_seconds`: Time between trades

### 3. Add Bot Wallet

**Via API or UI:**
- Add wallet address (EVM address, 0x...)
- Add encrypted private key
- Link to bot

## 🧪 Testing Steps

### Step 1: Create Bot

1. Go to Admin Dashboard → Bot Management
2. Click "Create Bot"
3. Select "Volume Bot"
4. Fill in configuration:
   - Name: "SHARP Polygon Test"
   - Chain: "polygon"
   - Base Token: `0xb36b62929762acf8a9cc27ecebf6d353ebb48244`
   - Quote Token: `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359`
   - Daily Volume: $100
   - Min Trade: $5
   - Max Trade: $10
   - Interval: 5-10 minutes
5. Save bot

### Step 2: Add Wallet

1. Go to bot details
2. Add wallet:
   - Wallet address (EVM format: 0x...)
   - Private key (will be encrypted)
3. Verify wallet has funds:
   - POL for gas
   - USDC for trades

### Step 3: Start Bot

1. Click "Start" on bot
2. Check Railway logs for:
   ```
   📊 EVM Volume bot {id} starting main loop...
   Initializing Uniswap client for Polygon
   ✅ Uniswap client initialized
   Base token: 0xb36b6292...
   Quote token: 0x3c499c54...
   ```

### Step 4: Monitor First Trade

**Watch Railway Logs:**
```
📊 EVM Volume bot {id} - Checking daily target...
Target: $100.00, Today: $0.00
Using wallet: 0x...
✅ EVM signer initialized: 0x...
Trade size: $7.50
Side: buy
🔄 Executing buy trade...
Buy: $7.50 = 7500000 smallest units
Quote obtained
Executing swap...
✅ Trade successful! TX: 0x...
```

**Check PolygonScan:**
- Go to https://polygonscan.com/tx/{tx_hash}
- Verify transaction details:
  - From: Your wallet address
  - To: Universal Router (0x643770E279d5D0733F21d6DC03A8efbABf3255B4)
  - Value: 0 (token swap)
  - Status: Success

### Step 5: Verify Stats Update

**Check Bot Stats:**
- Volume today should increase
- Trades today should increment
- Last trade timestamp should update

**Check Trade History:**
- Trade should appear in bot_trades table
- Side, amount, tx_signature should be recorded

## 🔍 Monitoring

### Railway Logs

**Watch for:**
- ✅ Successful trades
- ⚠️ Circuit breaker activity (if API issues)
- ❌ Errors (should be rare)

**Good Log Pattern:**
```json
{
  "level": "info",
  "logger": "app.bot_runner",
  "message": "Trade successful! TX: 0x...",
  "bot_id": "...",
  "side": "buy",
  "amount": 7.5
}
```

### PolygonScan

**Verify:**
- Transaction confirmed
- Gas used reasonable (~100k-300k gas)
- Tokens swapped correctly
- No failed transactions

### UI Dashboard

**Check:**
- Bot status: "running"
- Stats updating
- Trade history showing
- No error messages

## ⚠️ Troubleshooting

### Issue: Bot not starting

**Check:**
- Bot status in database (should be "running")
- Railway logs for errors
- Chain configuration correct
- Token addresses valid

### Issue: No trades executing

**Check:**
- Wallet has funds (POL + USDC)
- Daily target not reached
- Bot status still "running"
- Logs for errors

### Issue: Transaction fails

**Check:**
- Gas price reasonable
- Slippage tolerance sufficient
- Token approvals set (Permit2)
- Sufficient balance

### Issue: Circuit breaker opens

**Check:**
- Uniswap API status
- RPC endpoint working
- Network connectivity
- Will auto-recover after 60 seconds

## ✅ Success Criteria

- [ ] Bot starts successfully
- [ ] First buy trade executes (USDC → SHARP)
- [ ] Transaction confirmed on PolygonScan
- [ ] Stats update correctly
- [ ] Second trade executes (SHARP → USDC or another buy)
- [ ] Bot runs for 1+ hour without errors
- [ ] Multiple trades recorded
- [ ] Daily volume tracking works

## 📊 Expected Behavior

**First Hour:**
- 6-12 trades (5-10 min intervals)
- Mix of buy/sell trades
- Volume accumulating toward $100 target
- All trades successful

**After Target Reached:**
- Bot sleeps until midnight
- No more trades until next day
- Stats reset at midnight

## 🚨 Rollback Plan

If issues occur:

1. **Stop bot immediately:**
   ```bash
   curl -X POST https://trading-bridge-production.up.railway.app/bots/{id}/stop
   ```

2. **Check logs** for error details

3. **Fix issues** and redeploy

4. **Restart bot** when ready

## 📝 Notes

- **Gas costs:** ~$0.001 per swap on Polygon
- **Slippage:** 0.5% default (50 bps)
- **Approvals:** Permit2 approvals set automatically
- **Backward compatibility:** Solana bots unaffected

## 🎯 Next Steps After Testing

If testing successful:
1. Increase daily volume target
2. Add more wallets
3. Test on other chains (Arbitrum, Base)
4. Monitor for 24 hours
5. Scale to production volumes
