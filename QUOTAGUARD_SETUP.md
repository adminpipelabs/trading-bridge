# QuotaGuard Static IP Setup Guide

## ✅ Code Updated!

The code has been updated to automatically use QuotaGuard proxy when configured. You just need to:
1. Get your proxy URL from QuotaGuard
2. Add it to Railway environment variables
3. Whitelist your static IPs with BitMart

---

## Step 1: Get Your Static IP Addresses

1. **Log into QuotaGuard Dashboard**
   - Go to: https://www.quotaguard.com/
   - Navigate to your account dashboard

2. **Find Your Static IPs**
   - Look for "Static IPs" or "IP Addresses" section
   - You should see **two IP addresses** (primary + backup for redundancy)
   - Example format: `52.1.2.3` and `52.1.2.4`

3. **Copy Both IPs** - You'll need these for BitMart whitelisting

---

## Step 2: Get Your Proxy URL

In QuotaGuard dashboard, find:
- **Proxy URL** or **Endpoint URL**
- Format will be something like: `http://username:password@static.quotaguard.com:9293`
- Or check the "Integration" or "Setup" section for your proxy details

**Note:** You'll need your QuotaGuard username and password for the proxy URL.

**Common QuotaGuard proxy formats:**
- `http://username:password@static.quotaguard.com:9293`
- `http://username:password@us-east-1.static.quotaguard.com:9293` (if region-specific)

---

## Step 3: Configure Railway Environment Variables

1. **Go to Railway Dashboard**
   - Navigate to your `trading-bridge` service
   - Click on **Variables** tab

2. **Add This Environment Variable:**

```bash
QUOTAGUARD_PROXY_URL=http://username:password@static.quotaguard.com:9293
```

**Replace:**
- `username` with your QuotaGuard username
- `password` with your QuotaGuard password
- The full proxy URL with your actual QuotaGuard proxy URL

**Example:**
```bash
QUOTAGUARD_PROXY_URL=http://myuser:mypass123@static.quotaguard.com:9293
```

**Optional (if QuotaGuard provides separate URLs):**
```bash
HTTP_PROXY=http://username:password@static.quotaguard.com:9293
HTTPS_PROXY=http://username:password@static.quotaguard.com:9293
```

---

## Step 4: Redeploy Railway Service

1. **After adding the environment variable**, Railway will automatically redeploy
2. **OR manually trigger:** Go to **Deployments** → **Redeploy**
3. **Wait for deployment to complete**

---

## Step 5: Whitelist IP with BitMart

1. **Contact BitMart Support** or use their API key management dashboard
2. **Provide both static IP addresses:**
   - Primary IP: `[Your Primary IP from Step 1]`
   - Backup IP: `[Your Backup IP from Step 1]`
3. **Tell them:** "These are for API key whitelisting for Pipe labs trading bot"

**Important:** Whitelist BOTH IPs (primary + backup) for redundancy.

---

## Step 6: Test the Setup

After configuration:

1. **Check Railway Logs**
   - Go to Railway → `trading-bridge` service → **Logs** tab
   - Look for: `"Using proxy for bitmart: http://..."` or similar messages
   - This confirms the proxy is being used

2. **Test BitMart API Connection**
   - Try to fetch balances or place a test order
   - Check logs for successful API calls

3. **Verify Your IP**
   - You can test by making an API call and checking BitMart logs
   - Or use a service like `https://api.ipify.org` through the proxy to verify

---

## What Was Updated in Code

✅ **`app/services/exchange.py`** - CCXT exchanges (BitMart, Binance, etc.) now use proxy  
✅ **`app/solana/jupiter_client.py`** - Jupiter API calls now use proxy  
✅ **`app/jupiter.py`** - Legacy Jupiter functions now use proxy  
✅ **`app/bot_health.py`** - Health check API calls now use proxy  

All code automatically reads `QUOTAGUARD_PROXY_URL` environment variable and uses it for all outbound HTTP/HTTPS requests.

---

## Troubleshooting

### If proxy doesn't work:
- ✅ Verify proxy URL format is correct (should start with `http://`)
- ✅ Check QuotaGuard dashboard for correct username/password
- ✅ Ensure Railway environment variable is named exactly `QUOTAGUARD_PROXY_URL`
- ✅ Check Railway logs for proxy connection errors
- ✅ Try using `HTTP_PROXY` and `HTTPS_PROXY` instead if `QUOTAGUARD_PROXY_URL` doesn't work

### If BitMart still blocks:
- ✅ Verify IPs are whitelisted correctly in BitMart dashboard
- ✅ Check that both primary AND backup IPs are whitelisted
- ✅ Confirm you're using the correct API key
- ✅ Wait a few minutes after whitelisting (can take time to propagate)

### To verify proxy is working:
- Check Railway logs for messages like: `"Using proxy for bitmart: http://..."`
- Make a test API call and check if it succeeds
- Compare your current IP (without proxy) vs the static IP (should match QuotaGuard IPs)
