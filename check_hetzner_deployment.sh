#!/bin/bash
# Quick script to check Hetzner deployment status
# Run on Hetzner: bash check_hetzner_deployment.sh

echo "=========================================="
echo "Hetzner Deployment Status Check"
echo "=========================================="
echo ""

APP_DIR="/opt/trading-bridge"
SERVICE_NAME="trading-bridge"

# Check 1: Latest commit
echo "📦 Check 1: Latest Git Commit"
echo "----------------------------------------"
cd "$APP_DIR"
LATEST_COMMIT=$(git log --oneline -1)
echo "Latest commit: $LATEST_COMMIT"
echo ""

# Check 2: Uncommitted changes
echo "📝 Check 2: Uncommitted Changes"
echo "----------------------------------------"
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  WARNING: There are uncommitted changes!"
    git status --short
else
    echo "✅ No uncommitted changes - clean working directory"
fi
echo ""

# Check 3: Service status
echo "🔧 Check 3: Service Status"
echo "----------------------------------------"
if systemctl list-units --type=service | grep -q "$SERVICE_NAME"; then
    systemctl status "$SERVICE_NAME" --no-pager -l | head -15
else
    echo "⚠️  Service '$SERVICE_NAME' not found in systemd"
    echo "   Checking if app is running via other method..."
    ps aux | grep -E 'uvicorn|trading-bridge|python.*main' | grep -v grep || echo "   No trading-bridge process found"
fi
echo ""

# Check 4: Recent logs
echo "📋 Check 4: Recent Logs (last 20 lines)"
echo "----------------------------------------"
if systemctl list-units --type=service | grep -q "$SERVICE_NAME"; then
    journalctl -u "$SERVICE_NAME" --no-pager -n 20 | tail -15
else
    echo "⚠️  Cannot check logs - service not found"
    echo "   Check logs manually if app is running via other method"
fi
echo ""

# Check 5: Key files updated
echo "📁 Check 5: Key Files Updated"
echo "----------------------------------------"
echo "Checking if critical files exist:"
[ -f "$APP_DIR/app/coinstore_connector.py" ] && echo "✅ coinstore_connector.py exists" || echo "❌ coinstore_connector.py missing"
[ -f "$APP_DIR/app/coinstore_adapter.py" ] && echo "✅ coinstore_adapter.py exists" || echo "❌ coinstore_adapter.py missing"
[ -f "$APP_DIR/app/bot_routes.py" ] && echo "✅ bot_routes.py exists" || echo "❌ bot_routes.py missing"
echo ""

# Check 6: Verify fixes in code
echo "🔍 Check 6: Verify Fixes in Code"
echo "----------------------------------------"
if grep -q "/trade/order/place" "$APP_DIR/app/coinstore_connector.py" 2>/dev/null; then
    echo "✅ Coinstore order endpoint fix: FOUND"
else
    echo "❌ Coinstore order endpoint fix: NOT FOUND"
fi

if grep -q "ordType" "$APP_DIR/app/coinstore_connector.py" 2>/dev/null; then
    echo "✅ Coinstore ordType fix: FOUND"
else
    echo "❌ Coinstore ordType fix: NOT FOUND"
fi

if grep -q "recent_trades" "$APP_DIR/app/bot_routes.py" 2>/dev/null; then
    echo "✅ Recent trades endpoint fix: FOUND"
else
    echo "❌ Recent trades endpoint fix: NOT FOUND"
fi
echo ""

echo "=========================================="
echo "✅ Deployment Check Complete"
echo "=========================================="
