# Questions for Dev - Hummingbot Credentials

## What We Need

To complete the Hummingbot integration, we need:

1. **Hummingbot API credentials**
   - Username
   - Password (or API key)
   - API URL (usually `http://localhost:8000`)

2. **Network access**
   - Is Hummingbot running locally or in cloud?
   - How should Railway connect to it? (Tailscale, direct, etc.)

---

## Questions to Ask Dev

### 1. **Do you have Hummingbot running?**

**Ask:**
> "Do we have Hummingbot API running? If so, where is it located?"

**Possible answers:**
- Local machine (need Tailscale VPN)
- Cloud server (need URL)
- Docker containers (need to check docker-compose.yml)

---

### 2. **Where are the credentials?**

**Ask:**
> "Where are the Hummingbot API credentials stored? Can you check docker-compose.yml or .env file?"

**Where to check:**
```bash
# Option 1: Docker compose
cat ~/hummingbot_files/docker-compose.yml | grep -i "api\|auth\|user\|pass"

# Option 2: Environment file
cat ~/hummingbot_files/.env | grep -i "api\|auth\|user\|pass"

# Option 3: Inside container
docker exec hummingbot-api env | grep -i "api\|auth\|user\|pass"
```

---

### 3. **How should Railway connect?**

**Ask:**
> "How should Trading Bridge (on Railway) connect to Hummingbot? Is it local or cloud?"

**Options:**
- **Local:** Need Tailscale VPN or ngrok tunnel
- **Cloud:** Need cloud URL
- **Same Railway project:** Use internal service URL

---

### 4. **Can you help set up the connection?**

**Ask:**
> "Can you help set up the network connection between Railway and Hummingbot?"

**What they can do:**
- Set up Tailscale VPN
- Deploy Hummingbot to Railway
- Configure network access
- Test the connection

---

## Quick Message Template

Copy/paste this to your dev:

---

**Hi! We've implemented the Hummingbot integration in Trading Bridge. To complete it, we need:**

1. **Hummingbot API credentials:**
   - Username
   - Password (or API key)
   - API URL

2. **Network setup:**
   - Is Hummingbot running locally or in cloud?
   - How should Railway connect to it?

**Can you help find the credentials and set up the connection? The code is already pushed and ready to deploy once we have these.**

**I can help with:**
- Finding credentials (we have a script: `find_hummingbot_creds.sh`)
- Setting up Tailscale VPN if needed
- Testing the connection

**Let me know what you find!**

---

## What Dev Can Do

### Option 1: Find Credentials
```bash
# Run the credential finder script
cd ~/ai-trading-ui
./find_hummingbot_creds.sh ~/hummingbot_files

# Or check manually
cat ~/hummingbot_files/docker-compose.yml | grep -i "api\|auth\|user\|pass"
```

### Option 2: Set Up Network

**If Hummingbot is local:**
- Set up Tailscale VPN
- Get Tailscale IP
- Share IP with you

**If Hummingbot should be in cloud:**
- Deploy Hummingbot to Railway
- Get service URL
- Share URL with you

### Option 3: Test Connection
```bash
# Test Hummingbot API
curl -u username:password http://localhost:8000/bot-orchestration/status
```

---

## What You Can Do While Waiting

1. **Check if Hummingbot is running:**
   ```bash
   docker ps | grep hummingbot
   ```

2. **Try to find credentials yourself:**
   ```bash
   cd ~/ai-trading-ui
   ./find_hummingbot_creds.sh ~/hummingbot_files
   ```

3. **Prepare Railway:**
   - Go to Railway dashboard
   - Open Trading Bridge service
   - Go to Variables tab
   - Be ready to add environment variables

---

## Once You Have Credentials

1. **Add to Railway:**
   - Go to Trading Bridge service → Variables
   - Add:
     - `HUMMINGBOT_API_URL`
     - `HUMMINGBOT_API_USERNAME`
     - `HUMMINGBOT_API_PASSWORD`

2. **Redeploy:**
   - Railway will auto-deploy
   - Check logs for errors

3. **Test:**
   ```bash
   curl https://trading-bridge-production.up.railway.app/bots
   ```

---

**TL;DR: Ask dev for Hummingbot API credentials and network setup help!**
