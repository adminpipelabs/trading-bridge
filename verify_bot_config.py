#!/usr/bin/env python3
"""Quick script to verify bot configuration in production database"""
import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # Find the SHARP Volume Bot - Coinstore
    result = db.execute(text("""
        SELECT 
            id,
            name,
            status,
            config,
            updated_at
        FROM bots
        WHERE name LIKE '%SHARP Volume Bot%Coinstore%'
        ORDER BY updated_at DESC
        LIMIT 1
    """))
    
    bot = result.fetchone()
    
    if not bot:
        print("❌ Bot not found!")
        exit(1)
    
    bot_id, name, status, config, updated_at = bot
    
    print(f"✅ Bot Found:")
    print(f"   ID: {bot_id}")
    print(f"   Name: {name}")
    print(f"   Status: {status}")
    print(f"   Updated: {updated_at}")
    print(f"\n📋 Configuration:")
    
    if isinstance(config, str):
        config = json.loads(config)
    
    # Expected values
    expected = {
        "daily_volume_usd": 5000,
        "min_trade_usd": 10,
        "max_trade_usd": 15,
        "interval_min_seconds": 900,
        "interval_max_seconds": 1500,
        "slippage_bps": 50
    }
    
    # Check each value
    all_match = True
    for key, expected_value in expected.items():
        actual_value = config.get(key)
        match = "✅" if actual_value == expected_value else "❌"
        print(f"   {match} {key}: {actual_value} (expected: {expected_value})")
        if actual_value != expected_value:
            all_match = False
    
    # Show any extra config keys
    extra_keys = set(config.keys()) - set(expected.keys())
    if extra_keys:
        print(f"\n   Additional config keys: {', '.join(extra_keys)}")
    
    if all_match:
        print(f"\n✅ All configuration values match!")
    else:
        print(f"\n⚠️  Some configuration values don't match!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
