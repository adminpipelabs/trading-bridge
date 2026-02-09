# Client Flow - How Balance Display Works

## Overview
This document explains the complete flow of how clients see bot balances, from bot creation to balance display.

## 1. Bot Creation Flow

### Admin Creates Bot
1. **Admin selects connector** (e.g., "coinstore", "bitmart") from dropdown in UI
2. **Frontend sends** `POST /bots/create` with:
   ```json
   {
     "name": "SHARP-VB-Coinstore",
     "account": "client_sharp",
     "connector": "coinstore",  // ← Value from dropdown
     "pair": "SHARP/USDT",
     "bot_type": "volume"
   }
   ```
3. **Backend stores** bot in `bots` table with `connector = "coinstore"`

### API Key Setup (Separate Step)
- Admin adds API keys via `/clients/{client_id}/connectors` endpoint
- Stored in `connectors` table with `name = "coinstore"` (or "Coinstore", case may vary)
- **Critical**: Bot's `connector` field must match connector's `name` field (case-insensitive)

## 2. Balance Fetching Flow

### When Client Views Dashboard

1. **Frontend loads bots**
   - Calls `GET /bots?account=client_sharp`
   - Gets list of bots with their `connector` values

2. **Frontend fetches balance for each bot**
   - Calls `GET /bots/{bot_id}/balance-and-volume`
   - This happens automatically for all bots (running or stopped)

3. **Backend balance endpoint process:**

   ```
   GET /bots/{bot_id}/balance-and-volume
   ↓
   Load bot from database
   ↓
   Get bot.connector value (e.g., "coinstore")
   ↓
   Get bot.account (e.g., "client_sharp")
   ↓
   Call sync_connectors_to_exchange_manager(bot.account)
     ↓
     Find client by account_identifier
     ↓
     Query connectors table WHERE client_id = client.id
     ↓
     For each connector:
       - Add to exchange_manager using connector.name
       - Store with lowercase key: connector.name.lower()
   ↓
   Look up exchange: account.connectors.get(bot.connector.lower())
   ↓
   If found:
     - Call exchange.fetch_balance()
     - Extract SHARP and USDT balances
     - Return Available | Locked | Volume
   ↓
   If NOT found:
     - Return error: "Exchange 'coinstore' not found"
   ```

## 3. The Matching Problem

**The Issue:**
- Bot has `connector = "coinstore"` (from creation)
- Connector in DB has `name = "Coinstore"` (capitalized)
- exchange_manager stores it as `"coinstore"` (lowercase)
- Lookup uses `bot.connector.lower()` = `"coinstore"` ✅ Should work!

**But if:**
- Connector in DB has `name = "Coinstore"` 
- exchange_manager stores as `"coinstore"` (lowercase)
- Bot has `connector = "Coinstore"` (capitalized)
- Lookup: `"coinstore".lower()` = `"coinstore"` ✅ Should still work!

**The Real Problem:**
- Connectors might not be syncing to exchange_manager at all
- Or connector doesn't exist in database for this client
- Or API keys are missing/empty

## 4. Current Flow Diagram

```
┌─────────────────┐
│  Admin Creates  │
│  Bot via UI     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Bot Saved to   │
│  DB: connector  │
│  = "coinstore"   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Admin Adds API  │
│  Keys (separate) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Connector Saved│
│  to DB: name =  │
│  "coinstore"    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Client Views   │
│  Dashboard      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend Calls │
│  /bots/{id}/    │
│  balance-and-   │
│  volume         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backend Syncs  │
│  Connectors     │
│  to exchange_   │
│  manager        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Lookup Exchange│
│  by connector   │
│  name           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch Balance  │
│  from Exchange  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Return:        │
│  Available |    │
│  Locked |      │
│  Volume        │
└─────────────────┘
```

## 5. Key Points

1. **Bot connector** comes from UI dropdown selection
2. **Connector name** in database must match (case-insensitive)
3. **exchange_manager** stores connectors with lowercase keys
4. **Balance fetch** happens for ALL bots (not just running)
5. **Multiple bots** with same API key show same balance ✅

## 6. Debugging Steps

Use the diagnostic endpoint:
```
GET /bots/{bot_id}/balance-debug
```

This shows:
- Bot's connector value
- Connectors in database (with their names)
- Connectors in exchange_manager (after sync)
- Whether they match
- Diagnosis summary
