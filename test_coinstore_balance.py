#!/usr/bin/env python3
"""
Test Coinstore balance fetching
Run on Hetzner: python3 test_coinstore_balance.py
"""
import asyncio
import os
import sys
from sqlalchemy import create_engine, text
from cryptography.fernet import Fernet

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.coinstore_connector import CoinstoreConnector

async def test_balance():
    """Test Coinstore balance fetching."""
    
    # Get credentials from environment or database
    DATABASE_URL = os.getenv("DATABASE_URL")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    
    if not DATABASE_URL or not ENCRYPTION_KEY:
        print("❌ DATABASE_URL or ENCRYPTION_KEY not set")
        print("   Set these environment variables and try again")
        return False
    
    print("=" * 60)
    print("Coinstore Balance Test")
    print("=" * 60)
    print("")
    
    # Load credentials from database
    fernet = Fernet(ENCRYPTION_KEY.encode())
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                ec.api_key_encrypted, 
                ec.api_secret_encrypted,
                cl.account_identifier
            FROM exchange_credentials ec
            JOIN clients cl ON cl.id = ec.client_id
            WHERE ec.exchange = 'coinstore'
            LIMIT 1
        """))
        
        row = result.fetchone()
        if not row:
            print("❌ No Coinstore credentials found in database")
            return False
        
        api_key_encrypted = row[0]
        api_secret_encrypted = row[1]
        account = row[2]
        
        # Decrypt
        api_key = fernet.decrypt(api_key_encrypted.encode()).decode().strip()
        api_secret = fernet.decrypt(api_secret_encrypted.encode()).decode().strip()
        
        print(f"✅ Loaded credentials for account: {account}")
        print(f"   API Key: {api_key[:10]}...{api_key[-5:]}")
        print(f"   Secret: {api_secret[:5]}...{api_secret[-3:]}")
        print("")
    
    # Create connector (no proxy on Hetzner)
    connector = CoinstoreConnector(api_key, api_secret, proxy_url=None)
    
    try:
        print("📡 Fetching balance from Coinstore...")
        print("   Endpoint: POST /api/spot/accountList")
        print("")
        
        # Fetch balance
        response = await connector.get_balances()
        
        print("=" * 60)
        print("Response Received")
        print("=" * 60)
        print("")
        
        # Check response
        code = response.get('code', 'unknown')
        msg = response.get('msg', '')
        data = response.get('data', [])
        
        print(f"Response Code: {code}")
        print(f"Message: {msg}")
        print(f"Data Type: {type(data)}")
        print("")
        
        if code == 0 or code == "0":
            print("✅ SUCCESS! Balance fetch working!")
            print("")
            
            if isinstance(data, list):
                print(f"Found {len(data)} account entries:")
                print("")
                
                # Group by currency
                balances = {}
                for entry in data:
                    currency = entry.get('currency', 'UNKNOWN')
                    balance = float(entry.get('balance', 0))
                    balance_type = entry.get('type', 0)
                    type_name = entry.get('typeName', 'UNKNOWN')
                    
                    if currency not in balances:
                        balances[currency] = {'available': 0, 'frozen': 0}
                    
                    # Type 1 = AVAILABLE, Type 4 = FROZEN
                    if balance_type == 1 or type_name == 'AVAILABLE':
                        balances[currency]['available'] += balance
                    elif balance_type == 4 or type_name == 'FROZEN':
                        balances[currency]['frozen'] += balance
                
                # Display balances
                print("Balances:")
                print("-" * 60)
                for currency, amounts in sorted(balances.items()):
                    available = amounts['available']
                    frozen = amounts['frozen']
                    total = available + frozen
                    
                    if total > 0:
                        print(f"  {currency:8s}  Available: {available:>15.8f}  Frozen: {frozen:>15.8f}  Total: {total:>15.8f}")
                
                print("")
                print("✅ Balance fetching is working correctly!")
                return True
            else:
                print(f"⚠️  Unexpected data format: {type(data)}")
                print(f"   Data: {data}")
                return False
        else:
            print(f"❌ Error: Code {code}, Message: {msg}")
            if code == 1401:
                print("")
                print("⚠️  1401 Unauthorized - IP whitelist may not be active yet")
                print("   Wait 1-2 minutes after whitelisting and try again")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching balance: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await connector.close()

if __name__ == "__main__":
    success = asyncio.run(test_balance())
    sys.exit(0 if success else 1)
