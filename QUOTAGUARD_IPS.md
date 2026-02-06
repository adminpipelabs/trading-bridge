# Your QuotaGuard Static IPs

## Static IP Addresses

**Primary IP:** `3.222.129.4`  
**Backup IP:** `54.205.35.75`

---

## Next Steps

### ✅ Step 1: Get Your Proxy URL
From QuotaGuard dashboard, find your proxy URL. It should look like:
```
http://username:password@static.quotaguard.com:9293
```

### ✅ Step 2: Add to Railway
Go to Railway → `trading-bridge` service → **Variables** tab

Add:
```bash
QUOTAGUARD_PROXY_URL=http://username:password@static.quotaguard.com:9293
```
(Replace with your actual QuotaGuard proxy URL)

### ✅ Step 3: Whitelist IPs with BitMart
Contact BitMart support or use their API key management dashboard.

**Provide these IPs for whitelisting:**
- `3.222.129.4` (Primary)
- `54.205.35.75` (Backup)

**Message to BitMart:**
> "Please whitelist these IP addresses for our API key:
> - 3.222.129.4 (Primary)
> - 54.205.35.75 (Backup)
> 
> These are for Pipe labs trading bot API access."

### ✅ Step 4: Redeploy Railway
After adding the environment variable, Railway will auto-redeploy, or manually trigger from Deployments tab.

---

## Verification

After setup, check Railway logs for:
- `"Using proxy for bitmart: http://..."` - confirms proxy is active
- Successful BitMart API calls - confirms IP whitelisting worked
