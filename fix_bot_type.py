#!/usr/bin/env python3
"""
Fix bot_type for the Sharp bot that has NULL bot_type.
Run: python fix_bot_type.py
"""
import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(DATABASE_URL)
    
    bot_id = "74d9b480-f15b-444d-a290-a798b59c584a"
    bot_name = "Sharp-SB-BitMart"
    
    # Determine bot_type from name - "SB" likely means "Spread Bot"
    # But let's check the strategy field
    with engine.connect() as conn:
        # Check current state
        result = conn.execute(text("""
            SELECT id, name, bot_type, strategy, status 
            FROM bots 
            WHERE id = :bot_id
        """), {"bot_id": bot_id})
        
        row = result.fetchone()
        if not row:
            print(f"❌ Bot {bot_id} not found")
            sys.exit(1)
        
        print(f"Current bot state:")
        print(f"  ID: {row[0]}")
        print(f"  Name: {row[1]}")
        print(f"  Bot Type: {row[2]}")
        print(f"  Strategy: {row[3]}")
        print(f"  Status: {row[4]}")
        
        # Determine bot_type from strategy or name
        strategy = row[3] or ""
        name = row[1] or ""
        
        if "SB" in name.upper() or "spread" in name.lower():
            new_bot_type = "spread"
        elif "vol" in name.lower() or "volume" in name.lower() or strategy == "volume":
            new_bot_type = "volume"
        else:
            # Default to spread if unclear
            new_bot_type = "spread"
        
        print(f"\n🔧 Updating bot_type to: {new_bot_type}")
        
        # Update bot_type
        conn.execute(text("""
            UPDATE bots 
            SET bot_type = :bot_type 
            WHERE id = :bot_id
        """), {"bot_type": new_bot_type, "bot_id": bot_id})
        
        conn.commit()
        
        # Verify
        result2 = conn.execute(text("""
            SELECT bot_type FROM bots WHERE id = :bot_id
        """), {"bot_id": bot_id})
        
        updated = result2.fetchone()[0]
        print(f"✅ Updated! Bot type is now: {updated}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
