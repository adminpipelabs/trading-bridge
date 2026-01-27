# Manual Redeploy Instructions

## If Railway Auto-Deploy Isn't Working

### Option 1: Trigger Redeploy via Railway Dashboard

1. Go to Railway Dashboard → `trading-bridge` service
2. Click **"Settings"** tab
3. Scroll to **"Deploy"** section
4. Click **"Redeploy"** button
5. Select **"Deploy latest commit"**

### Option 2: Check Auto-Deploy Settings

1. Railway Dashboard → `trading-bridge` service
2. **Settings** → **"Source"** tab
3. Verify:
   - ✅ **Auto-Deploy** is enabled
   - ✅ **Branch** is set to `main`
   - ✅ **Repository** is connected to `adminpipelabs/trading-bridge`

### Option 3: Force Push (if needed)

```bash
cd trading-bridge
git commit --allow-empty -m "Trigger Railway deployment"
git push origin main
```

### Option 4: Check Railway Logs

1. Railway Dashboard → `trading-bridge` service
2. **"Deployments"** tab
3. Check latest deployment status
4. **"Logs"** tab → Check for errors

---

## Verify Deployment

After redeploy, test:

```bash
# Should return dashboard data
curl https://trading-bridge-production.up.railway.app/api/exchange/dashboard/client_sharp

# Should return balance data
curl https://trading-bridge-production.up.railway.app/api/exchange/balance/client_sharp
```

---

## Current Status

✅ Code is pushed to GitHub (`origin/main`)
✅ Endpoints are working (tested and confirmed)
❓ Railway UI not showing new deployment (but code IS deployed)

**Action**: Try manual redeploy via Railway Dashboard if you want to see a new deployment entry.
