# Reset Volume Bot & Start Trading

## Issue
Volume bot shows $0 volume - bot is "Running" but not executing trades.

## Solution

### Step 1: Reset Bot's last_trade_time (Run in Railway PostgreSQL)

Go to **Railway → PostgreSQL → Query tab** and run:

```sql
-- Reset Volume Bot for immediate execution
UPDATE bots 
SET last_trade_time = NULL,
    health_message = 'Reset for immediate execution - market order will execute on next cycle'
WHERE name LIKE '%Volume Bot%Coinstore%'
  AND status = 'running';

-- Verify reset
SELECT id, name, status, last_trade_time, health_status, health_message
FROM bots
WHERE name LIKE '%Volume Bot%Coinstore%'
ORDER BY updated_at DESC
LIMIT 1;
```

**Expected result:** `last_trade_time` should be `NULL`

---

### Step 2: Start Trading Bridge App on Hetzner

**SSH to Hetzner:**
```bash
ssh root@5.161.64.209
```

**Start the app:**
```bash
cd /opt/trading-bridge

# Activate virtual environment
source venv/bin/activate

# Start the app (choose one method):

# Option A: Run directly (for testing)
uvicorn app.main:app --host 0.0.0.0 --port 8080

# Option B: Run in background
nohup uvicorn app.main:app --host 0.0.0.0 --port 8080 > app.log 2>&1 &

# Option C: Create systemd service (recommended for production)
# See deploy_hetzner.sh for systemd setup
```

---

### Step 3: Verify Bot Runner is Active

**Check logs for bot runner activity:**
```bash
# If using systemd:
journalctl -u trading-bridge -f

# If running directly:
tail -f app.log | grep -E "CEX Bot Runner|Bot.*Found|EXECUTING TRADE"
```

**Look for:**
- `🔄 CEX Bot Runner cycle starting`
- `✅ Found X CEX bots`
- `✅✅✅ Bot {id} - FIRST TRADE - WILL EXECUTE MARKET ORDER NOW ✅✅✅`
- `🔄 EXECUTING TRADE NOW`
- `🔵 PLACING COINSTORE ORDER`

---

### Step 4: Check if Trade Executes

**Within 10-30 seconds after starting, you should see:**
- Log: `✅ Order placed successfully`
- Log: `INSERT INTO trade_logs` (or error if table missing)
- Database: `trade_logs` table should have new entry
- UI: Volume should update from $0 to > $0

---

## Troubleshooting

**If bot still doesn't trade:**

1. **Check bot runner is finding the bot:**
   ```bash
   # Look for: "✅ Found X CEX bots"
   journalctl -u trading-bridge -n 100 | grep "Found.*CEX bots"
   ```

2. **Check bot initialization:**
   ```bash
   # Look for: "✅ SUCCESS: Initialized CEX bot"
   journalctl -u trading-bridge -n 100 | grep "Initialized CEX bot"
   ```

3. **Check for errors:**
   ```bash
   journalctl -u trading-bridge -n 200 | grep -i error
   ```

4. **Verify database connection:**
   ```bash
   cd /opt/trading-bridge
   source venv/bin/activate
   python3 -c "import os; from app.database import get_db; print('DB OK' if os.getenv('DATABASE_URL') else 'DB URL missing')"
   ```

---

## Expected Timeline

- **0-10 seconds:** Bot runner finds bot, initializes
- **10-30 seconds:** First trade executes (if `last_trade_time` is NULL)
- **30-60 seconds:** Trade logged to database
- **60+ seconds:** UI shows updated volume

**If no trade after 60 seconds, check logs for errors.**
