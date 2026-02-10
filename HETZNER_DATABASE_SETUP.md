# Setup DATABASE_URL on Hetzner - Quick Guide

## Step 1: Get DATABASE_URL from Railway

1. Go to **Railway Dashboard**: https://railway.app/dashboard
2. Click on **PostgreSQL** service
3. Click **Variables** tab (or **Connect** tab)
4. Copy the `DATABASE_URL` value
   - Format: `postgresql://postgres:xxxxx@xxx.railway.app:5432/railway`
   - Or: `postgres://postgres:xxxxx@monorail.proxy.rlwy.net:12345/railway`

## Step 2: Add to Hetzner

**Option A: Using the script (recommended)**
```bash
ssh root@5.161.64.209
cd /opt/trading-bridge
bash setup_hetzner_database.sh "postgresql://postgres:xxxxx@xxx.railway.app:5432/railway"
```

**Option B: Manual setup**
```bash
ssh root@5.161.64.209
cd /opt/trading-bridge
nano .env

# Add this line:
DATABASE_URL=postgresql://postgres:xxxxx@xxx.railway.app:5432/railway

# Save and exit (Ctrl+X, Y, Enter)

# Restart app
pkill -f "uvicorn app.main:app"
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8080 > app.log 2>&1 &
```

## Step 3: Verify

```bash
# Check logs
tail -f /opt/trading-bridge/app.log | grep -E "CEX bot runner|Bot.*Found|EXECUTING TRADE"
```

**Look for:**
- `✅ CEX bot runner started`
- `✅ Found X CEX bots`
- `✅✅✅ Bot {id} - FIRST TRADE - WILL EXECUTE MARKET ORDER NOW`

## Expected Result

Within 30-60 seconds after restart:
- Bot runner starts
- Volume bot loads
- First trade executes
- Volume updates from $0 to > $0 in UI
