# URGENT: Dev Advice Needed - Two Critical Issues

**Status:** Live customers affected - need dev guidance before making changes

**Date:** February 7, 2026

---

## Issue 1: "Failed to fetch" when starting bot

**Problem:** When user clicks "Start Bot", they get "Failed to fetch" error.

**What we've tried:**
1. Fixed Request injection in backend (removed `= None` default, reordered parameters)
2. Added error logging in frontend
3. Added network error catching

**Current state:**
- Backend syntax error fixed (parameter ordering)
- Frontend has detailed logging
- But still getting "Failed to fetch"

**Questions for dev:**
1. Is `POST /bots/{bot_id}/start` the correct endpoint?
2. What headers are required? (X-Wallet-Address? Authorization?)
3. Should we check Railway logs for actual errors?
4. Is there a CORS issue we're missing?
5. Can you test the endpoint directly and share what works?

---

## Issue 2: Multiple bots trying to start simultaneously

**Problem:** When user clicks "Start Bot" on ONE bot, ANOTHER bot also tries to start automatically, then gets "Failed to fetch" error.

**What this suggests:**
- There might be event handler attached to multiple buttons
- Or there's a race condition in the bot list rendering
- Or the `onStartStop` handler is being called multiple times

**Code location:**
- Frontend: `ai-trading-ui/src/pages/ClientDashboard.jsx` - `handleStartStop` function
- Frontend: Bot list rendering with Start/Stop buttons

**Questions for dev:**
1. Is this expected behavior? Should starting one bot trigger others?
2. Could this be a React event handler issue (multiple handlers attached)?
3. Should we add debouncing or prevent multiple simultaneous requests?
4. Is there a bug in how the bot list is rendered (duplicate buttons)?

---

## What We Need

**Before making more changes, please advise:**

1. **For Issue 1 (Failed to fetch):**
   - What's the correct way to call the start endpoint?
   - What should we check in Railway logs?
   - Is there a known issue with this endpoint?

2. **For Issue 2 (Multiple bots starting):**
   - Is this a known bug?
   - Should we prevent multiple simultaneous start requests?
   - How should the UI handle this?

3. **Priority:**
   - Which issue should we fix first?
   - Are there workarounds for customers?

---

## Current Code State

**Backend:** `ec830b8` - Fixed Request injection syntax
**Frontend:** `bf802ab` - Added error logging

**Recent changes:**
- Fixed parameter ordering in `start_bot`, `stop_bot`, `update_bot` endpoints
- Added detailed console logging in frontend
- Added network error catching

---

## Environment

- **Frontend:** `app.pipelabs.xyz`
- **Backend:** `trading-bridge-production.up.railway.app`
- **Client:** `client_new_sharp_foundation`

---

**Please advise before we make more changes. We've been going in circles and don't want to break things further for live customers.**
