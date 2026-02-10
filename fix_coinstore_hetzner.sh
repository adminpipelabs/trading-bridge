#!/bin/bash
# Automatic Coinstore fix for Hetzner
# Run: bash fix_coinstore_hetzner.sh

set -e

cd /opt/trading-bridge
source venv/bin/activate

echo "=========================================="
echo "COINSTORE HETZNER FIX"
echo "=========================================="
echo ""

# Step 1: Check environment
echo "📋 Step 1: Checking environment..."
SERVER_IP="5.161.64.209"
echo "   Server IP: $SERVER_IP"
echo ""

# Check if proxy is set (should be empty on Hetzner)
if [ -n "$QUOTAGUARDSTATIC_URL" ] || [ -n "$QUOTAGUARD_PROXY_URL" ]; then
    echo "⚠️  WARNING: Proxy environment variables are set:"
    [ -n "$QUOTAGUARDSTATIC_URL" ] && echo "   QUOTAGUARDSTATIC_URL is set"
    [ -n "$QUOTAGUARD_PROXY_URL" ] && echo "   QUOTAGUARD_PROXY_URL is set"
    echo ""
    echo "   On Hetzner, you don't need proxy (static IP)."
    echo "   Consider unsetting these if Coinstore fails."
    echo ""
else
    echo "✅ No proxy configured (correct for Hetzner)"
    echo ""
fi

# Step 2: Test API
echo "📡 Step 2: Testing Coinstore API..."
echo ""

python3 test_coinstore_direct.py

echo ""
echo "=========================================="
echo "NEXT STEPS"
echo "=========================================="
echo ""
echo "If you see 1401 error:"
echo "  1. Check Coinstore dashboard → API Key 42b5c7c40bf625e7fcffd16a654b6ed0"
echo "  2. Verify IP $SERVER_IP is in IP binding list"
echo "  3. Verify API secret matches database (no extra spaces)"
echo "  4. Check API permissions: Read ✅ Spot Trading ✅"
echo ""
echo "If test succeeds but bots don't work:"
echo "  1. Check bot logs: journalctl -u trading-bridge -f"
echo "  2. Restart service: systemctl restart trading-bridge"
echo ""
