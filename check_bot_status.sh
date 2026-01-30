#!/bin/bash
# Quick bot status checker

BOT_ID="726186c7-0f5e-44a2-8c7e-b2e01186c0e4"
ADMIN_WALLET="BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV"
API_URL="https://trading-bridge-production.up.railway.app"

echo "🤖 Bot Status Check"
echo "=================="
echo ""

# Bot info
echo "📊 Bot Info:"
BOT_INFO=$(curl -s "$API_URL/bots/$BOT_ID" -H "X-Wallet-Address: $ADMIN_WALLET")
echo "$BOT_INFO" | jq '{
  name,
  status,
  bot_type,
  daily_target: .config.daily_volume_usd,
  volume_today: .stats.volume_today,
  trades_today: .stats.trades_today,
  last_trade: .stats.last_trade_at,
  error
}'
echo ""

# Wallets
echo "💼 Configured Wallets:"
WALLETS=$(curl -s "$API_URL/bots/$BOT_ID/wallets" -H "X-Wallet-Address: $ADMIN_WALLET")
echo "$WALLETS" | jq '.[] | {wallet: .wallet_address, added: .created_at}'
WALLET_COUNT=$(echo "$WALLETS" | jq 'length')
echo ""
echo "Total wallets: $WALLET_COUNT"
echo ""

# Health check
echo "🏥 Service Health:"
curl -s "$API_URL/health" | jq '{status, bot_runner}'
echo ""

# Check if trades are happening
VOLUME_TODAY=$(echo "$BOT_INFO" | jq -r '.stats.volume_today // 0')
TRADES_TODAY=$(echo "$BOT_INFO" | jq -r '.stats.trades_today // 0')

if [ "$VOLUME_TODAY" != "0" ] || [ "$TRADES_TODAY" != "0" ]; then
    echo "✅ TRADES DETECTED!"
    echo "   Volume today: \$$VOLUME_TODAY"
    echo "   Trades today: $TRADES_TODAY"
else
    echo "⏳ No trades yet (bot runs every 15-45 min)"
    echo "   Check Railway logs for trade attempts"
fi
