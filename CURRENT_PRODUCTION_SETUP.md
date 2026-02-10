# Current Production Setup

**Date:** February 10, 2026

---

## 🎯 **Current Architecture**

### **Backend (Trading Bridge API):**
- **Location:** Hetzner VPS
- **IP:** `5.161.64.209`
- **Status:** ✅ Running (primary)
- **Port:** 8080
- **Service:** `systemctl status trading-bridge`

### **Frontend (UI):**
- **Location:** Railway
- **Repository:** `ai-trading-ui`
- **URL:** `https://app.pipelabs.xyz`
- **Status:** ⚠️ Build failing (syntax error)

### **Database:**
- **Location:** Railway Postgres
- **Status:** ✅ Running
- **Used by:** Hetzner backend (connects via `DATABASE_URL`)

### **Railway Backend (Optional):**
- **Status:** Can run or be stopped
- **IP:** `162.220.232.99` (static IP)
- **Purpose:** Redundancy/backup (optional)

---

## 🤖 **Where Bots Execute**

**Bots run on:** Hetzner (`5.161.64.209`)

**Why:**
- Backend API is on Hetzner
- Bot runner executes on the same server as the API
- Bots connect to exchanges from Hetzner IP

**IP Whitelisting:**
- ✅ `5.161.64.209` (Hetzner) - **PRIMARY** - bots execute here
- ✅ `162.220.232.99` (Railway) - optional backup

---

## 📋 **What Clients See**

**Frontend URL:** `https://app.pipelabs.xyz`

**Frontend connects to:**
- Backend API on Hetzner (or Railway if running)
- Needs `REACT_APP_TRADING_BRIDGE_URL` environment variable

**Current Issue:**
- Frontend build failing (syntax error line 18:12)
- UI not deploying to Railway
- Clients see old version until build is fixed

---

## ✅ **Summary**

| Component | Location | IP | Status | Purpose |
|-----------|----------|-----|--------|---------|
| **Backend API** | Hetzner | `5.161.64.209` | ✅ Running | Primary - bots execute here |
| **Frontend UI** | Railway | - | ⚠️ Build failing | Client interface |
| **Database** | Railway | - | ✅ Running | Shared by Hetzner |
| **Railway Backend** | Railway | `162.220.232.99` | ⚠️ Optional | Backup/redundancy |

**Bots execute on:** Hetzner (`5.161.64.209`)

---

## 🔧 **To Test Bots**

**Bots are running on Hetzner:**
```bash
# SSH to Hetzner
ssh root@5.161.64.209

# Check bot status
systemctl status trading-bridge
journalctl -u trading-bridge -f
```

**API endpoint (if accessible):**
```bash
# Backend API on Hetzner
curl http://5.161.64.209:8080/api/bots
```

---

**Bottom line:** Backend and bots run on Hetzner. Frontend on Railway (but build is broken).
