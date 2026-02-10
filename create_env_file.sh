#!/bin/bash
# Create .env file for Hetzner deployment

cat > /opt/trading-bridge/.env << 'EOF'
DATABASE_URL=postgresql://postgres:MQNSwgpfxGMmrlFXEKXPhcOKGEiINpEf@switchback.proxy.rlwy.net:14406/railway
ENCRYPTION_KEY=8kxL2nP9qR7tY4wZ1aB3cD5eF6gH8iJ0kL2mN4oP6qR=
SERVER_IP=5.161.64.209
EOF

echo "✅ .env file created at /opt/trading-bridge/.env"
echo ""
echo "Contents:"
cat /opt/trading-bridge/.env
