#!/bin/bash
# Script to get BitMart credentials from Hummingbot and add to trading-bridge

# Get Hummingbot API URL from environment or use default
HUMMINGBOT_API_URL="${HUMMINGBOT_API_URL:-http://localhost:8000}"
HUMMINGBOT_USERNAME="${HUMMINGBOT_API_USERNAME:-admin}"
HUMMINGBOT_PASSWORD="${HUMMINGBOT_API_PASSWORD:-admin}"

echo "Attempting to get BitMart credentials from Hummingbot..."
echo "Hummingbot API: $HUMMINGBOT_API_URL"

# Try to get credentials from Hummingbot API (if endpoint exists)
# Note: This may not work if Hummingbot doesn't expose credentials endpoint
CREDS=$(curl -s -u "$HUMMINGBOT_USERNAME:$HUMMINGBOT_PASSWORD" \
  "$HUMMINGBOT_API_URL/api/credentials/client_sharp/bitmart" 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$CREDS" ]; then
  echo "✅ Got credentials from Hummingbot API"
  echo "$CREDS"
else
  echo "❌ Could not get credentials from Hummingbot API"
  echo ""
  echo "Please provide BitMart credentials manually:"
  echo ""
  echo "Option 1: From Hummingbot container"
  echo "  docker exec -it hummingbot-api cat bots/credentials/client_sharp/connectors/bitmart.yml"
  echo ""
  echo "Option 2: From local files"
  echo "  cat /path/to/hummingbot/bots/credentials/client_sharp/connectors/bitmart.yml"
  echo ""
  echo "Then run:"
  echo "  curl -X PUT 'https://trading-bridge-production.up.railway.app/clients/70ab29b1-66ad-4645-aec8-fa2f55abe144/connector' \\"
  echo "    -H 'Content-Type: application/json' \\"
  echo "    -d '{\"name\": \"bitmart\", \"api_key\": \"...\", \"api_secret\": \"...\", \"memo\": \"...\"}'"
fi
