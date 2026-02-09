#!/usr/bin/env python3
"""
Complete Diagnostic Script - Shows EXACTLY what's wrong
Run this to see why balance and trading aren't working
"""
import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_db
from app.services.exchange import exchange_manager
from app.api.client_data import sync_connectors_to_exchange_manager
from app.coinstore_connector import CoinstoreConnector
from app.security import decrypt_credential

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/trading_bridge')

async def diagnose():
    print("=" * 80)
    print("COMPLETE DIAGNOSTIC - What's Actually Wrong")
    print("=" * 80)
    print()
    
    # Create database session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Check bots
        print("1️⃣ CHECKING BOTS...")
        bots = db.execute(text("""
            SELECT id, name, status, connector, account, bot_type, pair
            FROM bots
            ORDER BY created_at DESC
            LIMIT 10
        """)).fetchall()
        
        if not bots:
            print("   ❌ NO BOTS FOUND in database")
            return
        
        print(f"   ✅ Found {len(bots)} bot(s)")
        for bot in bots:
            print(f"      - {bot.name} (ID: {bot.id})")
            print(f"        Status: {bot.status}")
            print(f"        Connector: {bot.connector}")
            print(f"        Account: {bot.account}")
            print(f"        Type: {bot.bot_type}")
            print()
        
        # 2. Check API keys for first bot
        bot = bots[0]
        print(f"2️⃣ CHECKING API KEYS for bot: {bot.name}")
        
        # Get client
        client = db.execute(text("""
            SELECT id, account_identifier, name
            FROM clients
            WHERE account_identifier = :account
        """), {"account": bot.account}).fetchone()
        
        if not client:
            print(f"   ❌ NO CLIENT FOUND for account: {bot.account}")
            return
        
        print(f"   ✅ Found client: {client.name} (ID: {client.id})")
        
        # Check exchange_credentials
        creds = db.execute(text("""
            SELECT exchange, api_key, api_secret, encrypted
            FROM exchange_credentials
            WHERE client_id = :client_id AND exchange = :exchange
        """), {"client_id": client.id, "exchange": bot.connector}).fetchone()
        
        if not creds:
            print(f"   ❌ NO API KEYS FOUND in exchange_credentials table")
            print(f"      Exchange: {bot.connector}")
            print(f"      Client ID: {client.id}")
            return
        
        print(f"   ✅ Found API keys in exchange_credentials")
        print(f"      Exchange: {creds.exchange}")
        print(f"      Encrypted: {creds.encrypted}")
        print(f"      API Key (first 10): {creds.api_key[:10]}..." if creds.api_key else "      API Key: None")
        
        # 3. Try to decrypt
        print()
        print("3️⃣ TESTING DECRYPTION...")
        try:
            if creds.encrypted:
                api_key = decrypt_credential(creds.api_key)
                api_secret = decrypt_credential(creds.api_secret) if creds.api_secret else None
            else:
                api_key = creds.api_key
                api_secret = creds.api_secret
            
            print(f"   ✅ Decryption successful")
            print(f"      API Key (first 10): {api_key[:10]}...")
            print(f"      API Secret (first 10): {api_secret[:10]}..." if api_secret else "      API Secret: None")
        except Exception as e:
            print(f"   ❌ DECRYPTION FAILED: {e}")
            return
        
        # 4. Try to sync to exchange_manager
        print()
        print("4️⃣ TESTING SYNC TO EXCHANGE_MANAGER...")
        try:
            synced = await sync_connectors_to_exchange_manager(bot.account, db)
            if synced:
                print(f"   ✅ Sync successful")
            else:
                print(f"   ❌ SYNC FAILED")
                return
        except Exception as e:
            print(f"   ❌ SYNC ERROR: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 5. Try to get account from exchange_manager
        print()
        print("5️⃣ TESTING EXCHANGE_MANAGER...")
        account = exchange_manager.get_account(bot.account)
        if not account:
            print(f"   ❌ ACCOUNT NOT FOUND in exchange_manager")
            return
        
        print(f"   ✅ Account found in exchange_manager")
        print(f"      Connectors: {list(account.connectors.keys())}")
        
        # 6. Try to fetch balance
        print()
        print("6️⃣ TESTING BALANCE FETCH...")
        try:
            balances = await account.get_balances()
            print(f"   ✅ Balance fetch successful!")
            print(f"      Response: {balances}")
            
            # Check if balances are empty
            if not balances or all(isinstance(v, dict) and v.get('error') for v in balances.values()):
                print(f"   ⚠️  WARNING: Balances are empty or have errors")
                for exchange, data in balances.items():
                    if isinstance(data, dict) and 'error' in data:
                        print(f"      {exchange}: ERROR - {data['error']}")
        except Exception as e:
            print(f"   ❌ BALANCE FETCH FAILED: {e}")
            import traceback
            traceback.print_exc()
        
        # 7. Test direct API call (Coinstore)
        if bot.connector.lower() == 'coinstore':
            print()
            print("7️⃣ TESTING DIRECT COINSTORE API CALL...")
            try:
                connector = CoinstoreConnector(api_key, api_secret)
                balance_data = await connector.get_balances()
                print(f"   ✅ Direct API call successful!")
                print(f"      Response code: {balance_data.get('code')}")
                print(f"      Response data: {balance_data.get('data')}")
            except Exception as e:
                print(f"   ❌ DIRECT API CALL FAILED: {e}")
                import traceback
                traceback.print_exc()
        
        # 8. Check bot runner status
        print()
        print("8️⃣ CHECKING BOT RUNNER STATUS...")
        # Check if bot is running
        if bot.status == 'running':
            print(f"   ✅ Bot status is 'running'")
            print(f"      Bot should be picked up by CEX runner")
        else:
            print(f"   ⚠️  Bot status is '{bot.status}' (not running)")
            print(f"      Bot won't trade until status is 'running'")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
