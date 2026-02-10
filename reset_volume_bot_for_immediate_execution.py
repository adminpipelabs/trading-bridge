#!/usr/bin/env python3
"""Reset last_trade_time to NULL for Volume Bot to force immediate execution"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    print("Set it with: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    print("🔄 Resetting Volume Bot for immediate execution...\n")
    
    # Find Volume Bot
    bot_result = db.execute(text("""
        SELECT id, name, status, last_trade_time
        FROM bots
        WHERE name LIKE '%Volume Bot%Coinstore%'
        ORDER BY updated_at DESC
        LIMIT 1
    """)).first()
    
    if not bot_result:
        print("❌ Volume Bot not found!")
        sys.exit(1)
    
    bot_id = bot_result.id
    bot_name = bot_result.name
    last_trade_time = bot_result.last_trade_time
    
    print(f"✅ Found bot: {bot_name}")
    print(f"   Bot ID: {bot_id}")
    print(f"   Current last_trade_time: {last_trade_time}\n")
    
    # Reset last_trade_time to NULL
    db.execute(text("""
        UPDATE bots 
        SET last_trade_time = NULL,
            health_message = 'Reset for immediate execution - market order will execute on next cycle'
        WHERE id = :bot_id
    """), {"bot_id": bot_id})
    db.commit()
    
    print("✅✅✅ SUCCESS: Reset last_trade_time to NULL")
    print("   Bot will execute market order immediately on next cycle (within 10 seconds)")
    print("   Check Hetzner logs for: '✅✅✅ Bot {id} - FIRST TRADE - WILL EXECUTE MARKET ORDER IMMEDIATELY ✅✅✅'\n")
    
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
