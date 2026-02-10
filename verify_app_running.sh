#!/bin/bash
# DEFINITIVE check if trading-bridge is running on Hetzner
# Run on Hetzner: bash verify_app_running.sh

echo "=========================================="
echo "TRADING-BRIDGE STATUS CHECK"
echo "=========================================="
echo ""

APP_DIR="/opt/trading-bridge"
SERVICE_NAME="trading-bridge"
PORT="8080"

# Check 1: Is process running?
echo "🔍 Check 1: Is Process Running?"
echo "----------------------------------------"
PROCESSES=$(ps aux | grep -E "uvicorn.*main:app|trading-bridge" | grep -v grep)
if [ -n "$PROCESSES" ]; then
    echo "✅ YES - Process found:"
    echo "$PROCESSES" | head -3
else
    echo "❌ NO - No trading-bridge process found"
fi
echo ""

# Check 2: Is port 8080 listening?
echo "🔍 Check 2: Is Port 8080 Listening?"
echo "----------------------------------------"
LISTENING=$(netstat -tlnp 2>/dev/null | grep ":$PORT " || ss -tlnp 2>/dev/null | grep ":$PORT ")
if [ -n "$LISTENING" ]; then
    echo "✅ YES - Port $PORT is listening:"
    echo "$LISTENING"
else
    echo "❌ NO - Port $PORT is NOT listening"
fi
echo ""

# Check 3: Can we connect to API?
echo "🔍 Check 3: Can We Connect to API?"
echo "----------------------------------------"
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:$PORT/health 2>/dev/null)
if [ "$HTTP_RESPONSE" = "200" ]; then
    echo "✅ YES - API responding (HTTP $HTTP_RESPONSE)"
    curl -s http://localhost:$PORT/health | head -3
elif [ -n "$HTTP_RESPONSE" ]; then
    echo "⚠️  API responding but error: HTTP $HTTP_RESPONSE"
else
    echo "❌ NO - Cannot connect to API (connection refused/timeout)"
fi
echo ""

# Check 4: Is systemd service running?
echo "🔍 Check 4: Is Systemd Service Running?"
echo "----------------------------------------"
if systemctl list-units --type=service --all | grep -q "$SERVICE_NAME"; then
    SERVICE_STATUS=$(systemctl is-active "$SERVICE_NAME" 2>/dev/null)
    if [ "$SERVICE_STATUS" = "active" ]; then
        echo "✅ YES - Service is active"
        systemctl status "$SERVICE_NAME" --no-pager -l | head -10
    else
        echo "❌ NO - Service exists but is $SERVICE_STATUS"
        systemctl status "$SERVICE_NAME" --no-pager -l | head -10
    fi
else
    echo "⚠️  Service '$SERVICE_NAME' not found in systemd"
fi
echo ""

# Check 5: Recent logs (last 30 seconds)
echo "🔍 Check 5: Recent Log Activity (last 30 seconds)"
echo "----------------------------------------"
if systemctl list-units --type=service --all | grep -q "$SERVICE_NAME"; then
    RECENT_LOGS=$(journalctl -u "$SERVICE_NAME" --since "30 seconds ago" --no-pager 2>/dev/null)
    if [ -n "$RECENT_LOGS" ]; then
        echo "✅ YES - Recent logs found:"
        echo "$RECENT_LOGS" | tail -5
    else
        echo "❌ NO - No logs in last 30 seconds"
    fi
elif [ -f "$APP_DIR/app.log" ]; then
    RECENT_LOGS=$(tail -20 "$APP_DIR/app.log" 2>/dev/null)
    if [ -n "$RECENT_LOGS" ]; then
        echo "✅ YES - Recent logs found in app.log:"
        echo "$RECENT_LOGS" | tail -5
    else
        echo "❌ NO - No logs in app.log"
    fi
else
    echo "⚠️  Cannot check logs - no systemd service or app.log found"
fi
echo ""

# Check 6: Bot Runner Activity
echo "🔍 Check 6: Bot Runner Activity"
echo "----------------------------------------"
if systemctl list-units --type=service --all | grep -q "$SERVICE_NAME"; then
    BOT_LOGS=$(journalctl -u "$SERVICE_NAME" --no-pager -n 200 | grep -E "CEX Bot Runner|Bot.*Found|EXECUTING TRADE" | tail -5)
else
    BOT_LOGS=$(tail -200 "$APP_DIR/app.log" 2>/dev/null | grep -E "CEX Bot Runner|Bot.*Found|EXECUTING TRADE" | tail -5)
fi

if [ -n "$BOT_LOGS" ]; then
    echo "✅ YES - Bot runner activity found:"
    echo "$BOT_LOGS"
else
    echo "❌ NO - No bot runner activity found"
fi
echo ""

# Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="

IS_RUNNING=false

if [ -n "$PROCESSES" ] && [ -n "$LISTENING" ]; then
    IS_RUNNING=true
    echo "✅ APP IS RUNNING"
    echo "   - Process: ✅"
    echo "   - Port listening: ✅"
    if [ "$HTTP_RESPONSE" = "200" ]; then
        echo "   - API responding: ✅"
    else
        echo "   - API responding: ⚠️"
    fi
else
    echo "❌ APP IS NOT RUNNING"
    echo "   - Process: ❌"
    echo "   - Port listening: ❌"
    echo "   - API responding: ❌"
fi

echo ""
if [ "$IS_RUNNING" = true ]; then
    echo "✅ CONFIRMED: Trading-bridge is running"
else
    echo "❌ CONFIRMED: Trading-bridge is NOT running"
    echo ""
    echo "To start it:"
    echo "  cd $APP_DIR"
    echo "  source venv/bin/activate"
    echo "  nohup uvicorn app.main:app --host 0.0.0.0 --port $PORT > app.log 2>&1 &"
fi
echo ""
