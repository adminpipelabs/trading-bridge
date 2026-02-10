#!/bin/bash
# Setup DATABASE_URL on Hetzner and restart app
# Usage: bash setup_hetzner_database.sh "postgresql://postgres:pass@host:port/db"

set -e

DATABASE_URL="$1"

if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL required"
    echo ""
    echo "Usage:"
    echo "  bash setup_hetzner_database.sh 'postgresql://postgres:xxxxx@xxx.railway.app:5432/railway'"
    echo ""
    echo "To get DATABASE_URL:"
    echo "  1. Railway Dashboard → PostgreSQL service → Variables tab"
    echo "  2. Copy DATABASE_URL value"
    echo "  3. Run this script with that value"
    exit 1
fi

APP_DIR="/opt/trading-bridge"
ENV_FILE="$APP_DIR/.env"
PORT="8080"

echo "=========================================="
echo "Setting up DATABASE_URL on Hetzner"
echo "=========================================="
echo ""

# Ensure .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    touch "$ENV_FILE"
fi

# Remove old DATABASE_URL if exists
if grep -q "^DATABASE_URL=" "$ENV_FILE" 2>/dev/null; then
    echo "⚠️  Removing existing DATABASE_URL..."
    sed -i '/^DATABASE_URL=/d' "$ENV_FILE"
fi

# Add DATABASE_URL
echo "DATABASE_URL=$DATABASE_URL" >> "$ENV_FILE"
echo "✅ DATABASE_URL added to .env"
echo ""

# Verify
echo "Verifying .env:"
grep "DATABASE_URL" "$ENV_FILE" | sed 's/:[^:@]*@/:***@/g'  # Hide password
echo ""

# Stop current app
echo "🛑 Stopping current app..."
pkill -f "uvicorn app.main:app" || echo "  (No process found to stop)"
sleep 2

# Start app with new DATABASE_URL
echo "🚀 Starting app with DATABASE_URL..."
cd "$APP_DIR"
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port "$PORT" > app.log 2>&1 &
APP_PID=$!

echo "✅ App started (PID: $APP_PID)"
echo ""

# Wait a moment for startup
sleep 3

# Check if running
if ps -p $APP_PID > /dev/null 2>&1; then
    echo "✅ App is running"
else
    echo "⚠️  App may have crashed - check logs:"
    echo "   tail -f $APP_DIR/app.log"
fi

echo ""
echo "📋 Next steps:"
echo "  1. Check logs: tail -f $APP_DIR/app.log"
echo "  2. Look for: '✅ CEX bot runner started'"
echo "  3. Look for: '✅✅✅ Bot {id} - FIRST TRADE - WILL EXECUTE MARKET ORDER NOW'"
echo ""
echo "✅ Setup complete!"
