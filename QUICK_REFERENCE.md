# Quick Reference Guide - Trading Bridge Production

**For:** Quick troubleshooting and common tasks  
**See:** `PRODUCTION_DOCUMENTATION.md` for full details

---

## 🚨 Common Issues & Quick Fixes

### **Bot Won't Start**
```bash
# Check bot runner status
curl http://5.161.64.209:8080/health/bot-runner

# Check database connection
ssh root@5.161.64.209 "cd /opt/trading-bridge && python3 -c 'from app.database import engine; print(engine)'"

# Restart app
ssh root@5.161.64.209 "cd /opt/trading-bridge && pkill -f uvicorn && source venv/bin/activate && export \$(cat .env | xargs) && nohup uvicorn app.main:app --host 0.0.0.0 --port 8080 > app.log 2>&1 &"
```

### **Balance Shows Zero**
```sql
-- Check if balance fetch is failing
SELECT health_message FROM bots WHERE id = 'bot-id';

-- Check API key permissions (must have "Read")
-- Go to Coinstore dashboard → API Management → Enable "Read"
```

### **Orders Not Placing (1401 Error)**
```bash
# Check recent logs for LIMIT order errors
ssh root@5.161.64.209 "tail -100 /opt/trading-bridge/app.log | grep -i '1401\|limit\|ordPrice'"

# See: SPREAD_BOT_LIMIT_ORDER_1401_HELP_REQUEST.md for details
```

### **Recent Activity Not Showing**
```sql
-- Check if orders are being logged
SELECT * FROM trade_logs WHERE bot_id = 'bot-id' ORDER BY created_at DESC LIMIT 10;

-- Should see entries with side='buy_placed' or 'sell_placed' for spread bot
```

---

## 📍 Key File Locations

| File | Purpose | Location |
|------|---------|----------|
| Main App | FastAPI entry | `app/main.py` |
| Bot Runner | Bot lifecycle | `app/bot_runner.py` |
| Spread Bot | Spread bot logic | `app/spread_bot.py` |
| Coinstore Connector | API wrapper | `app/coinstore_connector.py` |
| Bot Routes | API endpoints | `app/bot_routes.py` |
| Database Models | SQLAlchemy models | `app/database.py` |
| Logs | Application logs | `/opt/trading-bridge/app.log` |
| Config | Environment vars | `/opt/trading-bridge/.env` |

---

## 🔍 Debug Commands

### **Check App Status**
```bash
# Health check
curl http://5.161.64.209:8080/health

# Bot runner status
curl http://5.161.64.209:8080/health/bot-runner

# Check running processes
ssh root@5.161.64.209 "ps aux | grep uvicorn"
```

### **View Logs**
```bash
# Real-time logs
ssh root@5.161.64.209 "tail -f /opt/trading-bridge/app.log"

# Recent errors
ssh root@5.161.64.209 "tail -100 /opt/trading-bridge/app.log | grep -i error"

# Spread bot activity
ssh root@5.161.64.209 "tail -100 /opt/trading-bridge/app.log | grep -i spread"

# LIMIT order attempts
ssh root@5.161.64.209 "tail -100 /opt/trading-bridge/app.log | grep -i 'limit\|ordPrice\|1401'"
```

### **Database Queries**
```sql
-- Check bot status
SELECT id, name, status, health_status, health_message FROM bots;

-- Check recent trades
SELECT * FROM trade_logs ORDER BY created_at DESC LIMIT 20;

-- Check API credentials
SELECT exchange, client_id FROM exchange_credentials;
```

---

## 🔄 Common Workflows

### **Deploy New Code**
```bash
# 1. Push to GitHub
git add .
git commit -m "Description"
git push

# 2. Pull on Hetzner
ssh root@5.161.64.209 "cd /opt/trading-bridge && git pull origin main"

# 3. Restart app
ssh root@5.161.64.209 "cd /opt/trading-bridge && pkill -f uvicorn && source venv/bin/activate && export \$(cat .env | xargs) && nohup uvicorn app.main:app --host 0.0.0.0 --port 8080 > app.log 2>&1 &"

# 4. Verify
curl http://5.161.64.209:8080/health
```

### **Start a Bot**
```bash
# Via API
curl -X POST http://5.161.64.209:8080/bots/{bot-id}/start \
  -H "X-Wallet-Address: wallet-address"

# Or via database
UPDATE bots SET status = 'running' WHERE id = 'bot-id';
```

### **Check Bot Activity**
```bash
# Check logs
ssh root@5.161.64.209 "tail -100 /opt/trading-bridge/app.log | grep 'bot-id'"

# Check database
SELECT * FROM trade_logs WHERE bot_id = 'bot-id' ORDER BY created_at DESC LIMIT 10;
```

---

## ⚠️ Error Code Reference

| Code | Meaning | Common Cause | Fix |
|------|---------|--------------|-----|
| 1401 | Unauthorized | API permissions or payload | Check API key permissions, verify payload format |
| 401 | signature-failed | Signature calculation | Check JSON serialization, timestamp |
| 200 + error code | Application error | Various | Check error message in response body |

---

## 📞 Support Resources

- **Full Documentation:** `PRODUCTION_DOCUMENTATION.md`
- **LIMIT Order Issue:** `SPREAD_BOT_LIMIT_ORDER_1401_HELP_REQUEST.md`
- **Signature Issues:** `COINSTORE_SIGNATURE_BUG_REPORT.md`
- **Trade Logging:** `TRADE_DATA_STORAGE_AND_ACCESS.md`

---

**Last Updated:** February 10, 2026
