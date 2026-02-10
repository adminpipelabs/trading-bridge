#!/bin/bash
# Comprehensive Coinstore fix script
# Run on Hetzner: bash fix_coinstore_now.sh

set -e

echo "=========================================="
echo "COINSTORE FIX - COMPREHENSIVE CHECK"
echo "=========================================="
echo ""

cd /opt/trading-bridge
source venv/bin/activate

# Step 1: Check credentials
echo "📋 Step 1: Checking credentials from database..."
python3 << 'PYTHON_SCRIPT'
import os
import sys
from sqlalchemy import create_engine, text
from cryptography.fernet import Fernet

DATABASE_URL = os.getenv("DATABASE_URL")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not DATABASE_URL or not ENCRYPTION_KEY:
    print("❌ DATABASE_URL or ENCRYPTION_KEY not set")
    sys.exit(1)

fernet = Fernet(ENCRYPTION_KEY.encode())
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            ec.api_key_encrypted, 
            ec.api_secret_encrypted,
            b.id as bot_id,
            b.name as bot_name
        FROM exchange_credentials ec
        JOIN clients cl ON cl.id = ec.client_id
        JOIN bots b ON b.account = cl.account_identifier
        WHERE ec.exchange = 'coinstore' 
          AND b.connector = 'coinstore'
          AND b.status = 'running'
        ORDER BY b.name LIKE '%Coinstore%' DESC
        LIMIT 1
    """))
    
    row = result.fetchone()
    if not row:
        print("❌ No Coinstore credentials found")
        sys.exit(1)
    
    api_key = fernet.decrypt(row[0].encode()).decode()
    api_secret = fernet.decrypt(row[1].encode()).decode()
    bot_id = row[2]
    bot_name = row[3]
    
    print(f"✅ Bot: {bot_name} ({bot_id})")
    print(f"✅ API Key: {api_key}")
    print(f"✅ API Secret: {api_secret[:10]}...{api_secret[-5:]}")
    print(f"✅ Server IP: 5.161.64.209")
    print("")
    print("📝 VERIFY ON COINSTORE DASHBOARD:")
    print(f"   1. API Key: {api_key}")
    print(f"   2. IP Whitelist: 5.161.64.209")
    print(f"   3. Secret matches: {api_secret[:10]}...{api_secret[-5:]}")
PYTHON_SCRIPT

echo ""
echo "📡 Step 2: Testing Coinstore API..."
curl -s http://localhost:8080/test/coinstore | python3 -m json.tool || echo "❌ Test endpoint failed"

echo ""
echo "📊 Step 3: Checking bot logs..."
journalctl -u trading-bridge -n 100 --no-pager | grep -i "coinstore\|spread bot\|balance" | tail -20 || echo "No recent logs"

echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "✅ Credentials loaded"
echo "✅ Server IP: 5.161.64.209"
echo ""
echo "🔍 CHECK COINSTORE DASHBOARD:"
echo "   1. Is IP 5.161.64.209 whitelisted?"
echo "   2. Does API secret match?"
echo "   3. Are permissions enabled?"
echo ""
echo "📝 If still 1401, the issue is:"
echo "   - IP not whitelisted, OR"
echo "   - API secret wrong, OR"
echo "   - API key permissions missing"
echo ""
