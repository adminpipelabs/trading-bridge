#!/bin/bash
# Simple script to update Coinstore API key via API endpoint

# Configuration
API_URL="https://trading-bridge-production.up.railway.app/api/cex/credentials"
NEW_API_KEY="f2f0cb9e70c135e2cddfadc45c818cff"

echo "=========================================="
echo "Update Coinstore API Key"
echo "=========================================="
echo ""
echo "New API Key: $NEW_API_KEY"
echo "IP: 54.205.35.75 (matches Railway)"
echo ""
echo "⚠️  You need:"
echo "   1. API Secret for the new key"
echo "   2. Client ID (or wallet address for auth)"
echo ""

# Get secret
read -sp "Enter API Secret: " API_SECRET
echo ""

if [ -z "$API_SECRET" ]; then
    echo "❌ Secret required. Exiting."
    exit 1
fi

# Get client ID or wallet
read -p "Enter Client ID (or press Enter to use wallet auth): " CLIENT_ID

# Make API call
if [ -z "$CLIENT_ID" ]; then
    echo ""
    echo "Using wallet-based auth..."
    read -p "Enter Wallet Address: " WALLET_ADDRESS
    
    if [ -z "$WALLET_ADDRESS" ]; then
        echo "❌ Need either Client ID or Wallet Address"
        exit 1
    fi
    
    curl -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-Wallet-Address: $WALLET_ADDRESS" \
        -d "{
            \"exchange\": \"coinstore\",
            \"api_key\": \"$NEW_API_KEY\",
            \"api_secret\": \"$API_SECRET\"
        }"
else
    curl -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-Client-ID: $CLIENT_ID" \
        -d "{
            \"exchange\": \"coinstore\",
            \"api_key\": \"$NEW_API_KEY\",
            \"api_secret\": \"$API_SECRET\"
        }"
fi

echo ""
echo ""
echo "✅ Update complete!"
echo "   Wait 1-2 minutes, then refresh dashboard"
