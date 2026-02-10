#!/usr/bin/env python3
"""
Quick script to check bots in database for debugging.
Run: python check_bots_db.py
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    print("Set it with: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

# Convert Railway format if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(DATABASE_URL)
    
    print("🔍 Checking bots in database...")
    print("=" * 60)
    
    # Query for Sharp-related bots
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, bot_type, account, client_id, exchange, status, created_at 
            FROM bots 
            WHERE account LIKE '%sharp%' OR client_id LIKE '%sharp%' OR name LIKE '%sharp%'
            ORDER BY created_at DESC
            LIMIT 10;
        """))
        
        rows = result.fetchall()
        
        if not rows:
            print("❌ No bots found matching 'sharp'")
            print("\nChecking all recent bots...")
            result2 = conn.execute(text("""
                SELECT id, name, bot_type, account, client_id, exchange, status, created_at 
                FROM bots 
                ORDER BY created_at DESC
                LIMIT 10;
            """))
            rows = result2.fetchall()
        
        print(f"\nFound {len(rows)} bot(s):\n")
        
        for i, row in enumerate(rows, 1):
            print(f"Bot {i}:")
            print(f"  ID: {row[0]}")
            print(f"  Name: {row[1]}")
            print(f"  Bot Type: {row[2] or 'NULL'}")
            print(f"  Account: {row[3]}")
            print(f"  Client ID: {row[4]}")
            print(f"  Exchange: {row[5] or 'NULL'}")
            print(f"  Status: {row[6]}")
            print(f"  Created: {row[7]}")
            print("-" * 60)
        
        # Check for volume vs spread bots
        result3 = conn.execute(text("""
            SELECT bot_type, COUNT(*) as count
            FROM bots
            WHERE account LIKE '%sharp%' OR client_id LIKE '%sharp%'
            GROUP BY bot_type;
        """))
        
        type_counts = result3.fetchall()
        if type_counts:
            print("\nBot Type Breakdown:")
            for bot_type, count in type_counts:
                print(f"  {bot_type or 'NULL'}: {count}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
