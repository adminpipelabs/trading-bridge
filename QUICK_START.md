# Quick Start - Tailscale Setup

## ✅ Tailscale Installed!

**Next steps (run these commands):**

### Step 1: Start Tailscale

```bash
sudo tailscale up
```

**First time:** It will open a browser window to sign in/login to Tailscale.

---

### Step 2: Get Your Tailscale IP

After Tailscale is connected, run:

```bash
tailscale ip -4
```

**Example output:** `100.64.0.5`

**Save this IP!** You'll need it for Railway.

---

### Step 3: Set Railway Environment Variables

Go to Railway Dashboard:
1. Select **Trading Bridge** service
2. Go to **Variables** tab  
3. Click **+ New Variable**
4. Add these three variables:

```bash
HUMMINGBOT_API_URL=http://<your-tailscale-ip>:8000
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=admin
```

**Replace `<your-tailscale-ip>` with your actual IP from Step 2**

**Example:**
```bash
HUMMINGBOT_API_URL=http://100.64.0.5:8000
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=admin
```

---

### Step 4: Railway Auto-Redeploys

Railway will automatically redeploy when you add variables.

**Monitor deployment:**
- Go to **Deployments** tab
- Watch for successful deployment
- Check logs for any errors

---

### Step 5: Test Integration

After deployment completes, test:

```bash
# Get bots from Hummingbot
curl https://trading-bridge-production.up.railway.app/bots

# Should return bots from Hummingbot!
```

---

## Verify Everything Works

### Check Tailscale:
```bash
tailscale status
# Should show your machine as connected
```

### Check Hummingbot:
```bash
docker ps | grep hummingbot-api
# Should show hummingbot-api running
```

### Test Locally:
```bash
curl -u admin:admin http://localhost:8000/bot-orchestration/status
# Should return: {"status":"success","data":{}}
```

---

## Troubleshooting

### Tailscale not connecting?
- Make sure you're logged in: `tailscale status`
- Check if browser opened for login
- Try: `sudo tailscale up --reset`

### Can't reach Hummingbot from Railway?
- Verify Tailscale IP is correct
- Check Railway logs for connection errors
- Make sure Hummingbot is running: `docker ps | grep hummingbot-api`

### Railway deployment fails?
- Check Railway logs
- Verify environment variables are set correctly
- Make sure Tailscale IP format is correct (no trailing slash)

---

## Summary

**What you need to do:**

1. ✅ Run: `sudo tailscale up` (enter your password)
2. ✅ Run: `tailscale ip -4` (get your IP)
3. ✅ Set Railway variables with your Tailscale IP
4. ✅ Wait for Railway to redeploy
5. ✅ Test: `curl https://trading-bridge-production.up.railway.app/bots`

---

**Ready! Run `sudo tailscale up` to get started!** 🚀
