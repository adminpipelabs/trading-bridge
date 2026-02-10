#!/bin/bash
# Setup DATABASE_URL on Hetzner
# Usage: bash setup_database_url.sh "postgresql://user:pass@host:port/db"

DATABASE_URL="$1"

if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL required"
    echo "Usage: bash setup_database_url.sh 'postgresql://user:pass@host:port/db'"
    exit 1
fi

APP_DIR="/opt/trading-bridge"
ENV_FILE="$APP_DIR/.env"

echo "=========================================="
echo "Setting up DATABASE_URL on Hetzner"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    touch "$ENV_FILE"
fi

# Check if DATABASE_URL already exists
if grep -q "^DATABASE_URL=" "$ENV_FILE" 2>/dev/null; then
    echo "⚠️  DATABASE_URL already exists in .env"
    echo "Current value:"
    grep "^DATABASE_URL=" "$ENV_FILE"
    echo ""
    read -p "Overwrite? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
    # Remove old DATABASE_URL line
    sed -i '/^DATABASE_URL=/d' "$ENV_FILE"
fi

# Add DATABASE_URL
echo "DATABASE_URL=$DATABASE_URL" >> "$ENV_FILE"
echo "✅ DATABASE_URL added to .env"

# Verify
echo ""
echo "Verifying .env file:"
grep "DATABASE_URL" "$ENV_FILE"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next: Restart the app for changes to take effect"
