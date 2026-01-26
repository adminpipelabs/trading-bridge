# Tailscale VPN Setup Guide

## Quick Setup (5 minutes)

### Step 1: Install Tailscale

**macOS:**
```bash
brew install tailscale
```

**Or download from:** https://tailscale.com/download

---

### Step 2: Start Tailscale

```bash
sudo tailscale up
```

**First time:** It will open a browser window to sign in/login.

---

### Step 3: Get Your Tailscale IP

```bash
tailscale ip -4
```

**Example output:** `100.64.0.5`

**Save this IP!** You'll need it for Railway.

---

### Step 4: Verify Hummingbot is Accessible

From another machine (or Railway), test:

```bash
curl -u admin:admin http://<your-tailscale-ip>:8000/bot-orchestration/status
```

Should return: `{"status":"success","data":{}}`

---

### Step 5: Set Railway Environment Variables

Go to Railway Dashboard:
1. Select **Trading Bridge** service
2. Go to **Variables** tab
3. Add these variables:

```bash
HUMMINGBOT_API_URL=http://<your-tailscale-ip>:8000
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=admin
```

**Example:**
```bash
HUMMINGBOT_API_URL=http://100.64.0.5:8000
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=admin
```

---

### Step 6: Redeploy Trading Bridge

Railway will auto-redeploy when you add variables, or:
1. Go to **Deployments** tab
2. Click **Redeploy**

---

### Step 7: Test Integration

After deployment, test:

```bash
# Get bots
curl https://trading-bridge-production.up.railway.app/bots

# Should return bots from Hummingbot!
```

---

## Troubleshooting

### Issue: Tailscale not connecting
**Solution:** Make sure you're logged in: `tailscale status`

### Issue: Can't reach Hummingbot
**Solution:** 
- Check Tailscale IP: `tailscale ip -4`
- Verify Hummingbot is running: `docker ps | grep hummingbot-api`
- Test locally: `curl -u admin:admin http://localhost:8000/bot-orchestration/status`

### Issue: Railway can't connect
**Solution:**
- Verify Tailscale IP is correct
- Check Railway logs for connection errors
- Make sure Tailscale is running: `tailscale status`

---

## Security Note

**For production:** Change the default password (`admin`) or use Railway deployment instead.

---

**Ready to set up!** 🚀
