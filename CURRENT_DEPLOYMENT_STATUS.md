# Current Deployment Status - Quick Reference

**Date:** February 10, 2026

---

## 🏗️ **Current Architecture**

### **Backend (Trading Bridge API):**
- **Primary:** Hetzner VPS
  - IP: `5.161.64.209`
  - Status: ✅ Running
  - Port: 8080
  - Service: `systemctl status trading-bridge`
  - **Bots execute here**

- **Optional:** Railway
  - IP: `162.220.232.99` (static outbound)
  - Status: ⚠️ Can run (redundancy) or stopped (save costs)
  - **Currently:** Unknown if running

### **Frontend:**
- **Railway:** `ai-trading-ui` service
  - URL: `https://app.pipelabs.xyz`
  - Status: ⚠️ Build failing (syntax error)
  - **Clients see this UI**

### **Database:**
- **Railway Postgres**
  - Both backends connect to this
  - Contains: bots, credentials, configs, trades

---

## 🎯 **Where Bots Run**

**Bots execute on:** Hetzner (`5.161.64.209`)

**Why:**
- Hetzner has static IP (no proxy needed)
- IP whitelisted on exchanges
- Direct connection to Coinstore/BitMart
- More reliable than Railway proxy setup

---

## 📊 **Current Issue: Zero Balances**

**Problem:** Bot shows "Running" but balances are 0

**Bot:** SHARP Volume Bot - Coinstore

**What to check:**
1. Is balance endpoint being called? (Browser Network tab)
2. Is backend returning balance data? (Hetzner logs)
3. Is bot runner actually fetching balances? (Hetzner logs)
4. Are exchange credentials loaded? (Database check)

---

## ✅ **What's Working**

- ✅ Coinstore API connection (balance fetching works)
- ✅ BitMart API connection (balance fetching works)
- ✅ Bot creation
- ✅ Bot shows as "Running"

---

## ❌ **What's Not Working**

- ❌ UI shows 0 balances (Available, Locked, Volume, P&L all 0)
- ❌ Frontend build failing (syntax error - separate issue)

---

**Next:** Debug why balances show 0 despite bot running and API working.
