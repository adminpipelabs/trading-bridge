# Pipe Labs Backend Schema Mismatch

**Date:** 2026-01-27  
**Error:** `column clients.wallet_address does not exist`

---

## ❌ **Problem**

The **Pipe Labs backend** (`backend-pipelabs-dashboard`) is querying:
```sql
SELECT clients.id, clients.name, clients.wallet_address, clients.wallet_type, 
       clients.email, clients.password_hash, clients.status, clients.tier, 
       clients.role, clients.settings, clients.created_at, clients.updated_at 
FROM clients 
ORDER BY clients.created_at DESC
```

But the `clients` table in PostgreSQL doesn't have these columns yet.

---

## ✅ **What We Fixed**

**Trading Bridge (`trading-bridge`):**
- ✅ Added frontend-compatible columns to Client model
- ✅ Updated `/clients` endpoint to return all fields
- ✅ Called `/init-db` to recreate tables

**But:** The Pipe Labs backend has its own database schema and needs to be updated separately.

---

## 🔍 **Root Cause**

The Pipe Labs backend (`backend-pipelabs-dashboard`) has its own database models and is querying columns that don't exist. This is a **separate codebase** that needs to be updated.

---

## 📋 **Solution Options**

### Option 1: Update Pipe Labs Backend (Recommended)

The Pipe Labs backend needs to:
1. Add migration to add missing columns to `clients` table:
   - `wallet_address` (String, nullable)
   - `wallet_type` (String, nullable)
   - `email` (String, nullable)
   - `password_hash` (String, nullable)
   - `status` (String, default='active')
   - `tier` (String, nullable)
   - `role` (String, default='client')
   - `settings` (JSON, nullable)

2. Or update the query to not select these columns if they don't exist

### Option 2: Use Trading Bridge Endpoint

If Pipe Labs backend can be updated to call trading-bridge's `/clients` endpoint instead of querying database directly.

---

## 🎯 **Current Status**

- ✅ Trading Bridge schema updated
- ✅ Trading Bridge tables recreated with new columns
- ❌ Pipe Labs backend still expects old schema

**Next Step:** Update Pipe Labs backend codebase to match new schema or add migration.

---

**The error is coming from `backend-pipelabs-dashboard`, not `trading-bridge`. That codebase needs to be updated separately.**
