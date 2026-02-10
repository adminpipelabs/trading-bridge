# Hetzner Deployment Guide

**Server:** `ubuntu-2gb-ash-1`  
**IP:** `5.161.64.209`  
**Location:** Ashburn, VA

---

## 🎯 **Step 1: Whitelist IP on Exchanges**

**Before deploying, whitelist the IP:**

1. **BitMart:**
   - Go to BitMart API settings
   - Add IP: `5.161.64.209`
   - Save

2. **Coinstore:**
   - Go to Coinstore API settings
   - Add IP: `5.161.64.209` (if IP whitelist is required)
   - Save

---

## 🚀 **Step 2: SSH into Server**

```bash
ssh root@5.161.64.209
```

**Or if you have a different user:**
```bash
ssh your-username@5.161.64.209
```

---

## 📦 **Step 3: Install Dependencies**

```bash
# Update system
apt update && apt upgrade -y

# Install Python 3.11+ and pip
apt install -y python3.11 python3.11-venv python3-pip git

# Install PostgreSQL client (if needed)
apt install -y postgresql-client

# Install system dependencies
apt install -y build-essential libssl-dev libffi-dev
```

---

## 🔧 **Step 4: Clone Repository**

```bash
# Create app directory
mkdir -p /opt/trading-bridge
cd /opt/trading-bridge

# Clone repo (replace with your repo URL)
git clone https://github.com/adminpipelabs/trading-bridge.git .

# Or if you have SSH access:
# git clone git@github.com:adminpipelabs/trading-bridge.git .
```

---

## 🐍 **Step 5: Set Up Python Environment**

```bash
cd /opt/trading-bridge

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ **Step 6: Configure Environment Variables**

```bash
# Create .env file
nano /opt/trading-bridge/.env
```

**Add these variables:**
```bash
DATABASE_URL=postgresql+psycopg2://postgres:password@host:port/dbname
ENCRYPTION_KEY=your_encryption_key_here
QUOTAGUARDSTATIC_URL=  # Leave empty - not needed!
```

**Note:** Remove `QUOTAGUARDSTATIC_URL` or leave it empty - we don't need proxy anymore!

---

## 🗄️ **Step 7: Database Setup**

**Option A: Use existing Railway database**
- Keep `DATABASE_URL` pointing to Railway Postgres
- No changes needed

**Option B: Set up local Postgres**
```bash
apt install -y postgresql postgresql-contrib
# Then configure DATABASE_URL to point to local postgres
```

---

## 🚀 **Step 8: Run the Application**

**Option A: Direct run (for testing)**
```bash
cd /opt/trading-bridge
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**Option B: Systemd service (production)**
```bash
# Create service file
nano /etc/systemd/system/trading-bridge.service
```

**Service file content:**
```ini
[Unit]
Description=Trading Bridge API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/trading-bridge
Environment="PATH=/opt/trading-bridge/venv/bin"
ExecStart=/opt/trading-bridge/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
systemctl daemon-reload
systemctl enable trading-bridge
systemctl start trading-bridge
systemctl status trading-bridge
```

---

## 🔥 **Step 9: Configure Firewall**

```bash
# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp  # If running on port 8080

# Enable firewall
ufw enable
```

---

## ✅ **Step 10: Verify**

```bash
# Check if app is running
curl http://localhost:8080/health

# Check logs
journalctl -u trading-bridge -f
```

---

## 🔄 **Step 11: Remove Proxy Code (Optional)**

Since we don't need proxy anymore, we can simplify the code:

1. Remove `QUOTAGUARDSTATIC_URL` from env vars
2. Remove proxy configuration from code
3. Direct API calls (no proxy)

**But this is optional - the code will work fine with proxy disabled.**

---

## 📝 **Notes**

- **Static IP:** `5.161.64.209` - whitelist this on exchanges
- **No proxy needed** - direct connections
- **Same codebase** - just deploy to Hetzner instead of Railway
- **Database** - can use Railway Postgres or local Postgres

---

## 🐛 **Troubleshooting**

**Can't SSH:**
- Check Hetzner firewall settings
- Verify SSH key is added to server

**App won't start:**
- Check Python version: `python3 --version` (need 3.11+)
- Check dependencies: `pip list`
- Check logs: `journalctl -u trading-bridge -n 50`

**Database connection fails:**
- Verify `DATABASE_URL` is correct
- Check if Railway Postgres allows connections from Hetzner IP
- Test connection: `psql $DATABASE_URL`

---

**Ready to deploy!** Start with Step 2 (SSH) and let me know if you need help with any step.
