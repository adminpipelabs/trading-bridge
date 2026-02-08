#!/usr/bin/env python3
"""
Check Sharp's BitMart connectors in the database.
Run this to diagnose why exchange isn't initializing.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

# Handle Railway's postgres:// format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print("=" * 80)
print("CHECKING SHARP'S BITMART CONNECTORS")
print("=" * 80)
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
print()

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Query connectors for Sharp
    query = text("""
        SELECT 
            c.id,
            c.name as connector_name,
            c.memo,
            c.api_key IS NOT NULL as has_api_key,
            c.api_secret IS NOT NULL as has_api_secret,
            c.client_id,
            cl.account_identifier,
            cl.name as client_name
        FROM connectors c
        LEFT JOIN clients cl ON cl.id = c.client_id
        WHERE cl.account_identifier = 'client_new_sharp_foundation'
           OR cl.account_identifier LIKE '%sharp%'
           OR c.name ILIKE '%bitmart%'
           OR c.name ILIKE '%sharp%'
        ORDER BY c.created_at DESC;
    """)
    
    result = db.execute(query)
    rows = result.fetchall()
    
    if not rows:
        print("❌ NO CONNECTORS FOUND!")
        print()
        print("This means:")
        print("1. No connector row exists for Sharp's BitMart API keys")
        print("2. The connector might be in 'exchange_credentials' table (encrypted)")
        print("3. The client_id might not match")
        print()
        print("Checking clients table...")
        
        # Check clients table
        client_query = text("""
            SELECT id, account_identifier, name, wallet_address
            FROM clients
            WHERE account_identifier = 'client_new_sharp_foundation'
               OR account_identifier LIKE '%sharp%'
               OR name ILIKE '%sharp%'
        """)
        client_result = db.execute(client_query)
        client_rows = client_result.fetchall()
        
        if client_rows:
            print(f"✅ Found {len(client_rows)} client(s):")
            for row in client_rows:
                print(f"   - ID: {row[0]}, Account: {row[1]}, Name: {row[2]}")
        else:
            print("❌ No clients found either!")
        
        print()
        print("Checking exchange_credentials table (encrypted)...")
        creds_query = text("""
            SELECT 
                ec.id,
                ec.exchange,
                ec.client_id,
                ec.api_key_encrypted IS NOT NULL as has_api_key,
                ec.api_secret_encrypted IS NOT NULL as has_api_secret,
                cl.account_identifier
            FROM exchange_credentials ec
            LEFT JOIN clients cl ON cl.id = ec.client_id
            WHERE cl.account_identifier = 'client_new_sharp_foundation'
               OR cl.account_identifier LIKE '%sharp%'
               OR ec.exchange ILIKE '%bitmart%'
        """)
        creds_result = db.execute(creds_query)
        creds_rows = creds_result.fetchall()
        
        if creds_rows:
            print(f"✅ Found {len(creds_rows)} credential(s) in exchange_credentials table:")
            for row in creds_rows:
                print(f"   - Exchange: {row[1]}, Client: {row[5]}, Has API Key: {row[3]}, Has Secret: {row[4]}")
            print()
            print("⚠️  NOTE: Credentials are encrypted. Need to sync to 'connectors' table.")
        else:
            print("❌ No credentials found in exchange_credentials table either!")
        
    else:
        print(f"✅ Found {len(rows)} connector(s):")
        print()
        
        for i, row in enumerate(rows, 1):
            name_ok = '✅' if row[1] and row[1].lower() == 'bitmart' else '❌ WRONG - should be "bitmart"'
            memo_ok = '✅' if row[2] else '❌ MISSING - BitMart needs UID'
            key_ok = '✅' if row[3] else '❌ MISSING'
            secret_ok = '✅' if row[4] else '❌ MISSING'
            
            print(f"Connector #{i}:")
            print(f"  ID: {row[0]}")
            print(f"  Name: '{row[1]}' {name_ok}")
            print(f"  Memo: '{row[2]}' {memo_ok}")
            print(f"  Has API Key: {key_ok}")
            print(f"  Has API Secret: {secret_ok}")
            print(f"  Client ID: {row[5]}")
            print(f"  Account: {row[6]}")
            print(f"  Client Name: {row[7]}")
            print()
            
            # Check if name needs fixing
            if row[1] and row[1].lower() != 'bitmart':
                print(f"  ⚠️  FIX NEEDED: Name is '{row[1]}' but should be 'bitmart' (lowercase)")
                print(f"     Run: UPDATE connectors SET name = 'bitmart' WHERE id = '{row[0]}';")
                print()
            
            # Check if memo is missing
            if not row[2]:
                print(f"  ⚠️  FIX NEEDED: Memo/UID is missing")
                print(f"     Run: UPDATE connectors SET memo = 'YOUR_BITMART_UID' WHERE id = '{row[0]}';")
                print()
    
    db.close()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if rows:
        for row in rows:
            issues = []
            if not row[1] or row[1].lower() != 'bitmart':
                issues.append("connector name wrong")
            if not row[2]:
                issues.append("memo/UID missing")
            if not row[3]:
                issues.append("API key missing")
            if not row[4]:
                issues.append("API secret missing")
            
            if issues:
                print(f"❌ Connector {row[0]} has issues: {', '.join(issues)}")
            else:
                print(f"✅ Connector {row[0]} looks good!")
    else:
        print("❌ No connectors found - this is why exchange isn't initializing!")
        print("   Need to create connector row or sync from exchange_credentials table")
    
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
