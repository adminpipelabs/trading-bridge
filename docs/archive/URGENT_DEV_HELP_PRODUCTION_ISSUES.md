# URGENT: Production Issues - Need Dev Advice

**Status:** Live customers affected - need immediate guidance before making changes

**Date:** February 7, 2026

---

## Critical Production Issues

### Issue 1: Bot ON/OFF Status Not Visible
**Problem:** Users cannot see if their bot is ON or OFF in the dashboard.

**What we need to know:**
- What field/endpoint should we check to determine if a bot is running vs stopped?
- Is it `bot.status` (values: 'running', 'stopped')?
- Is it `bot.health_status` (values: 'healthy', 'stale', 'error')?
- Should we combine both fields?
- What's the correct way to display bot status in the UI?

**Current code location:**
- Frontend: `ai-trading-ui/src/pages/ClientDashboard.jsx` - Bot Status card
- Backend: `trading-bridge/app/bot_routes.py` - Bot status fields

---

### Issue 2: "Failed to start bot: Failed to fetch" Error
**Problem:** When users click "Start Bot", they get a network error.

**What we need to know:**
- What endpoint should the frontend call to start a bot?
- Current endpoint being called: `POST /bots/{bot_id}/start`
- What headers are required? (X-Wallet-Address, Authorization, etc.)
- Is there a CORS issue? (Frontend: `app.pipelabs.xyz`, Backend: `trading-bridge-production.up.railway.app`)
- Should we check Railway logs for errors on this endpoint?
- Is the endpoint working correctly in production?

**Current code location:**
- Frontend: `ai-trading-ui/src/services/api.js` - `startBot()` function
- Backend: `trading-bridge/app/bot_routes.py` - `start_bot()` endpoint

---

## Recent Changes (Rolled Back)

We rolled back recent changes to avoid further issues:
- **Backend:** Removed Request injection changes (commits dd61328, 5603d5f)
- **Frontend:** Removed error handling changes (commits 8956e2a, 5d2aa20)

**Current deployed state:**
- Backend: `c5b1d63` - "FIX: Add proper Pydantic model for bot update endpoint"
- Frontend: `68b9e0b` - "FIX: Show ON/OFF status based on bot.status, remove Volume Today and Volume 7d boxes"

---

## Questions for Dev

1. **Bot Status Display:**
   - What's the correct way to show if a bot is ON/OFF?
   - Which field(s) should we check?
   - What are the possible status values?

2. **Start Bot Endpoint:**
   - Is `POST /bots/{bot_id}/start` the correct endpoint?
   - What authentication/headers are required?
   - Can you check Railway logs for errors when this endpoint is called?
   - Is there a CORS configuration issue?

3. **Testing:**
   - Should we test with a specific bot ID?
   - What's the expected request/response format?

4. **Priority:**
   - Which issue should we fix first?
   - Are there any workarounds for customers right now?

---

## Environment Details

- **Frontend URL:** `app.pipelabs.xyz`
- **Backend URL:** `trading-bridge-production.up.railway.app`
- **Client Account:** `client_new_sharp_foundation`
- **Wallet Address:** `0xb4...85ae` (from user session)

---

**Please advise before we make any changes to avoid further disruption to live customers.**
