#!/bin/bash
# Script to re-add wallet with correct private key
# Usage: ./fix_wallet.sh YOUR_BASE58_PRIVATE_KEY

BOT_ID="726186c7-0f5e-44a2-8c7e-b2e01186c0e4"
WALLET_ADDRESS="BPaJfwA4iRVKjt2RoGNJGoJ26NtdFS86HX8po88W75vG"
ADMIN_WALLET="BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV"
API_URL="https://trading-bridge-production.up.railway.app"

if [ -z "$1" ]; then
    echo "❌ Error: Private key required"
    echo "Usage: ./fix_wallet.sh YOUR_BASE58_PRIVATE_KEY"
    echo ""
    echo "To get your private key:"
    echo "1. Open Phantom wallet"
    echo "2. Settings → Security & Privacy → Export Private Key"
    echo "3. Copy the base58 key (letters/numbers only)"
    exit 1
fi

PRIVATE_KEY="$1"

echo "🔄 Adding wallet with correct private key..."
echo "Wallet: $WALLET_ADDRESS"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL/bots/$BOT_ID/wallets" \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: $ADMIN_WALLET" \
  -d "{
    \"address\": \"$WALLET_ADDRESS\",
    \"private_key\": \"$PRIVATE_KEY\"
  }")

echo "Response:"
echo "$RESPONSE" | jq .

if echo "$RESPONSE" | jq -e '.wallet_address' > /dev/null 2>&1; then
    echo ""
    echo "✅ Wallet added successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Check Railway logs to see if bot picks up the wallet"
    echo "2. Bot should execute trades within 15-45 minutes"
else
    echo ""
    echo "❌ Failed to add wallet. Check the error above."
fi
