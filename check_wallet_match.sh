#!/bin/bash
# Check if login wallet matches trading wallet

WALLET="4vGfe6sSdXiNYL9SjuHqt3xaubPcSvyPzVBcX2r1VoE5"
BOT_ID="c659c814-81b6-488e-8cfa-9d3f82244de5"
API_URL="https://trading-bridge-production.up.railway.app"

echo "🔍 Checking wallet usage for: $WALLET"
echo ""

# 1. Check login wallet (client authentication)
echo "1. Login Wallet (Authentication):"
CLIENT_INFO=$(curl -s "${API_URL}/clients/by-wallet/${WALLET}" \
  -H "X-Wallet-Address: ${WALLET}" 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$CLIENT_INFO" ]; then
  echo "$CLIENT_INFO" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"   Client ID: {data.get('client_id', 'N/A')}\")
print(f\"   Client Name: {data.get('name', 'N/A')}\")
print(f\"   Login Wallets:\")
for wallet in data.get('wallets', []):
    print(f\"     - {wallet.get('address', 'N/A')} ({wallet.get('chain', 'N/A')})\")
" 2>/dev/null
else
  echo "   ❌ Not found"
fi

echo ""

# 2. Check trading wallet (bot execution)
echo "2. Trading Wallet (Bot Execution):"
BOT_INFO=$(curl -s "${API_URL}/bots/${BOT_ID}" \
  -H "X-Wallet-Address: ${WALLET}" 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$BOT_INFO" ]; then
  echo "   Bot ID: $BOT_ID"
  echo "   Bot Name: $(echo "$BOT_INFO" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("name", "N/A"))' 2>/dev/null)"
  echo ""
  echo "   ⚠️  Note: Trading wallet address is stored in bot_wallets table"
  echo "      Need to check database directly for bot_wallets.wallet_address"
fi

echo ""

# 3. Check trading_keys table (client-level key management)
echo "3. Trading Keys (Client Key Management):"
echo "   Checking if wallet has a trading key stored..."
# This would require database access - let me try via API if there's an endpoint

echo ""
echo "📋 Summary:"
echo "   Login Wallet: $WALLET (used for authentication)"
echo "   Trading Wallet: Need to check bot_wallets table in database"
echo ""
echo "   To verify if they match, we need to query:"
echo "   - bot_wallets.wallet_address WHERE bot_id = '$BOT_ID'"
echo "   - trading_keys.wallet_address WHERE client_id = 'ecb1aaa9-5f3b-48cf-9585-df22ca0b525f'"
