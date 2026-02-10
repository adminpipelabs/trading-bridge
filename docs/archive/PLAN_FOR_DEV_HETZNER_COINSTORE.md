# Plan for Dev - Hetzner Deployment (Coinstore First)

**Date:** February 10, 2026  
**Goal:** Deploy to Hetzner server and get Coinstore working (no proxy needed)

---

## 🎯 **What We're Doing**

**Moving from Railway + QuotaGuard (broken) to Hetzner VPS (direct connection)**

**Why:**
- QuotaGuard proxy is completely broken (all requests timeout)
- Hetzner server has static IP `5.161.64.209` already whitelisted on Coinstore
- No proxy needed - direct API calls will work
- Simpler, more reliable architecture

---

## 📋 **Current Status**

**Hetzner Server:**
- **IP:** `5.161.64.209`
- **Server:** `ubuntu-2gb-ash-1` (CPX11)
- **Status:** Running, root access available
- **Coinstore IP whitelist:** ✅ Already done (`5.161.64.209`)

**Code Status:**
- ✅ All fixes applied (correct API key, proxy handling)
- ✅ Automated deployment script created (`deploy_hetzner.sh`)
- ✅ Ready to deploy

---

## 🚀 **Deployment Plan**

### **Step 1: Deploy to Hetzner**

**Automated script does:**
1. Installs Python 3.11, git, dependencies
2. Clones repository from GitHub
3. Sets up Python virtual environment
4. Installs requirements.txt
5. Creates .env file template
6. Creates systemd service
7. Configures firewall

**Script location:** `deploy_hetzner.sh` (in repo)

**Run as root on Hetzner:**
```bash
curl -o deploy_hetzner.sh https://raw.githubusercontent.com/adminpipelabs/trading-bridge/main/deploy_hetzner.sh
chmod +x deploy_hetzner.sh
bash deploy_hetzner.sh
```

---

### **Step 2: Configure Environment**

**Edit .env file:**
```bash
nano /opt/trading-bridge/.env
```

**Set:**
- `DATABASE_URL` - Railway Postgres (or local Postgres)
- `ENCRYPTION_KEY` - Same as Railway
- No `QUOTAGUARDSTATIC_URL` needed!

---

### **Step 3: Start Service**

```bash
systemctl start trading-bridge
systemctl enable trading-bridge
systemctl status trading-bridge
```

---

### **Step 4: Test Coinstore**

**Check logs:**
```bash
journalctl -u trading-bridge -f
```

**Look for:**
- `📈 Spread bot ... starting for SHARP/USDT` (Coinstore bots)
- `💰 Balance: X SHARP, Y USDT` ← Should work!
- `📊 Mid price: ...`
- `📝 Placing buy/sell order...`

**Test endpoint:**
```bash
curl http://localhost:8080/test/coinstore
```

**Expected:**
- Status 200
- Balance response (not 1401)
- Success!

---

## ✅ **Why This Will Work**

1. **IP Already Whitelisted:** `5.161.64.209` is on Coinstore whitelist
2. **No Proxy:** Direct connection, no QuotaGuard dependency
3. **Same Code:** All fixes already applied
4. **Static IP:** Won't change, reliable

---

## 🎯 **Success Criteria**

**Coinstore bots should:**
- ✅ Fetch balances successfully
- ✅ Calculate mid prices
- ✅ Place orders
- ✅ No 1401 errors
- ✅ No proxy timeouts

---

## 📝 **Files Created**

1. `deploy_hetzner.sh` - Automated deployment script
2. `HETZNER_DEPLOYMENT_GUIDE.md` - Detailed guide
3. `PLAN_FOR_DEV_HETZNER_COINSTORE.md` - This file

---

## 🔄 **Next Steps**

1. **Deploy to Hetzner** - Run deployment script
2. **Configure .env** - Set DATABASE_URL and ENCRYPTION_KEY
3. **Start service** - systemctl start trading-bridge
4. **Test Coinstore** - Check logs and test endpoint
5. **Verify trading** - Confirm orders are being placed

---

**Once Coinstore works, we can add BitMart IP whitelist and test BitMart.**

**The code is ready. Just need to deploy and configure.**
