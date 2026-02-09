#!/bin/bash
# Query bots for a wallet address via API

WALLET="4vGfe6sSdXiNYL9SjuHqt3xaubPcSvyPzVBcX2r1VoE5"
API_URL="https://trading-bridge-production.up.railway.app"

echo "🔍 Checking wallet: $WALLET"
echo ""

# First, check if this wallet is registered as a client
echo "1. Checking if wallet is registered as client..."
CLIENT_INFO=$(curl -s "${API_URL}/clients/by-wallet/${WALLET}" \
  -H "X-Wallet-Address: ${WALLET}" 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$CLIENT_INFO" ]; then
  echo "✅ Found client info:"
  echo "$CLIENT_INFO" | python3 -m json.tool 2>/dev/null || echo "$CLIENT_INFO"
  echo ""
  
  # Extract account_identifier
  ACCOUNT=$(echo "$CLIENT_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('account_identifier', ''))" 2>/dev/null)
  
  if [ ! -z "$ACCOUNT" ]; then
    echo "2. Finding bots for account: $ACCOUNT"
    BOTS=$(curl -s "${API_URL}/bots?account=${ACCOUNT}" \
      -H "X-Wallet-Address: ${WALLET}" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ ! -z "$BOTS" ]; then
      echo "✅ Found bots:"
      echo "$BOTS" | python3 -m json.tool 2>/dev/null || echo "$BOTS"
    else
      echo "❌ No bots found or error querying bots"
    fi
  fi
else
  echo "❌ Wallet not found as client login wallet"
  echo ""
  echo "Note: This wallet might be a trading wallet (stored in bot_wallets or trading_keys)"
  echo "      but not a client login wallet. Check Railway database directly."
fi
