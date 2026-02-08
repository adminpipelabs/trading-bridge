#!/usr/bin/env python3
"""
Check Sharp's BitMart connector configuration in database.
Run this to verify connector name and memo/UID.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    print("Set it with: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

# Convert Railway's postgres:// to postgresql:// if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print("🔍 Checking Sharp's BitMart connectors...")
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'connected'}\n")

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
            cl.account_identifier,
            cl.name as client_name
        FROM connectors c
        LEFT JOIN clients cl ON cl.id = c.client_id
        WHERE cl.account_identifier LIKE '%sharp%'
           OR cl.account_identifier LIKE '%Sharp%'
           OR c.name ILIKE '%bitmart%'
           OR c.name ILIKE '%sharp%'
        ORDER BY c.created_at DESC
    """)
    
    results = db.execute(query).fetchall()
    
    if not results:
        print("❌ No connectors found matching 'sharp' or 'bitmart'")
        print("\nTrying broader search...")
        
        # Try to find any connectors
        all_connectors = db.execute(text("""
            SELECT 
                c.id,
                c.name,
                c.memo,
                cl.account_identifier,
                cl.name as client_name
            FROM connectors c
            LEFT JOIN clients cl ON cl.id = c.client_id
            ORDER BY c.created_at DESC
            LIMIT 10
        """)).fetchall()
        
        if all_connectors:
            print(f"\nFound {len(all_connectors)} connector(s) in database:")
            for row in all_connectors:
                print(f"  - Client: {row.client_name or row.account_identifier}, Connector: {row.name}, Memo: {row.memo or 'NULL'}")
        else:
            print("❌ No connectors found in database at all")
    else:
        print(f"✅ Found {len(results)} connector(s) matching Sharp/BitMart:\n")
        
        for row in results:
            connector_name = row.connector_name or "NULL"
            memo = row.memo or "NULL"
            has_key = "✅" if row.has_api_key else "❌"
            has_secret = "✅" if row.has_api_secret else "❌"
            
            print(f"📋 Connector ID: {row.id}")
            print(f"   Client: {row.client_name or row.account_identifier}")
            print(f"   Name: '{connector_name}'")
            print(f"   Memo/UID: {memo}")
            print(f"   API Key: {has_key}")
            print(f"   API Secret: {has_secret}")
            
            # Check if name is correct
            if connector_name.lower().strip() == "bitmart":
                print(f"   ✅ Name is correct: 'bitmart'")
            else:
                print(f"   ❌ Name should be exactly 'bitmart' (lowercase)")
                print(f"      Current: '{connector_name}'")
            
            # Check if memo is present
            if memo and memo != "NULL" and memo.strip():
                print(f"   ✅ Memo/UID is present: {memo[:10]}...")
            else:
                print(f"   ❌ Memo/UID is MISSING! BitMart REQUIRES this!")
                print(f"      This is likely why balance fetch is failing.")
            
            print()
        
        # Summary
        print("=" * 60)
        print("SUMMARY:")
        print("=" * 60)
        
        correct_name = any(r.connector_name and r.connector_name.lower().strip() == "bitmart" for r in results)
        has_memo = any(r.memo and r.memo.strip() for r in results)
        
        if correct_name and has_memo:
            print("✅ Connector name is correct ('bitmart')")
            print("✅ Memo/UID is present")
            print("\n✅ Configuration looks good! Check logs for other issues.")
        else:
            if not correct_name:
                print("❌ Connector name is NOT 'bitmart' (lowercase)")
                print("   Fix: UPDATE connectors SET name = 'bitmart' WHERE id = ...")
            if not has_memo:
                print("❌ Memo/UID is MISSING")
                print("   Fix: UPDATE connectors SET memo = 'YOUR_BITMART_UID' WHERE id = ...")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error querying database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
