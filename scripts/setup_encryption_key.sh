#!/bin/bash
# Generate and display ENCRYPTION_KEY for Railway
# Usage: ./scripts/setup_encryption_key.sh

echo "🔐 Generating ENCRYPTION_KEY..."
echo ""

# Generate key
KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

echo "✅ Generated ENCRYPTION_KEY:"
echo ""
echo "$KEY"
echo ""
echo "📋 To set in Railway:"
echo "   railway variables set ENCRYPTION_KEY='$KEY'"
echo ""
echo "Or copy the key above and add it manually in Railway Dashboard:"
echo "   Railway Dashboard → trading-bridge → Variables → Add Variable"
echo "   Name: ENCRYPTION_KEY"
echo "   Value: (paste the key above)"
echo ""
