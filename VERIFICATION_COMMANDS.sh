#!/bin/bash
# Verification Commands for Client Testing Setup
# Run these after migrations and ENCRYPTION_KEY are set

API_BASE="https://trading-bridge-production.up.railway.app"

echo "=========================================="
echo "VERIFICATION TESTS"
echo "=========================================="
echo ""

echo "1. Testing Health Monitor Endpoint..."
curl -s "${API_BASE}/bots/health/summary" | jq '.' || echo "❌ Health endpoint failed"
echo ""

echo "2. Testing Root Endpoint..."
curl -s "${API_BASE}/" | jq '.' || echo "❌ Root endpoint failed"
echo ""

echo "3. Testing Bots List Endpoint..."
curl -s "${API_BASE}/bots" | jq '.bots | length' || echo "❌ Bots endpoint failed"
echo ""

echo "=========================================="
echo "Manual Tests Required:"
echo "=========================================="
echo ""
echo "1. Login as Admin:"
echo "   - Should see Admin Dashboard"
echo "   - Should see all clients"
echo "   - Should see bot health statuses"
echo ""
echo "2. Login as Client (Lynk):"
echo "   - Should see Client Dashboard (NOT Admin)"
echo "   - Should see welcome modal (first time)"
echo "   - Should see Start/Stop/Edit buttons"
echo "   - Should NOT see Delete button"
echo "   - Should NOT see other clients' bots"
echo ""
echo "3. Test Authorization:"
echo "   - As client, try to start another client's bot"
echo "   - Should get 403 Forbidden error"
echo ""
echo "=========================================="
