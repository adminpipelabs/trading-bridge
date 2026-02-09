#!/usr/bin/env python3
"""
Check if Sharp's BitMart bot has executed any trades.
Queries the database for trade logs and bot status.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    print("   Set it from Railway: DATABASE_URL='postgresql://...'")
    sys.exit(1)

# Create database connection
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # Find Sharp's BitMart bot
    print("🔍 Looking for Sharp's BitMart bot...")
    bot_result = db.execute(text("""
        SELECT id, name, status, last_trade_time, health_message, stats
        FROM bots
        WHERE name LIKE '%BitMart%' OR name LIKE '%Sharp%'
        ORDER BY created_at DESC
        LIMIT 5
    """)).fetchall()
    
    if not bot_result:
        print("❌ No bot found with 'BitMart' or 'Sharp' in name")
        sys.exit(1)
    
    print(f"\n✅ Found {len(bot_result)} bot(s):\n")
    
    for bot in bot_result:
        bot_id = bot[0]
        bot_name = bot[1]
        status = bot[2]
        last_trade_time = bot[3]
        health_message = bot[4]
        stats = bot[5]
        
        print(f"📊 Bot: {bot_name}")
        print(f"   ID: {bot_id}")
        print(f"   Status: {status}")
        print(f"   Last Trade Time: {last_trade_time}")
        print(f"   Health Message: {health_message}")
        
        # Check trade_logs table (CEX trades)
        print(f"\n   Checking trade_logs table...")
        trade_logs = db.execute(text("""
            SELECT side, amount, price, cost_usd, order_id, created_at
            FROM trade_logs
            WHERE bot_id = :bot_id
            ORDER BY created_at DESC
            LIMIT 10
        """), {"bot_id": bot_id}).fetchall()
        
        if trade_logs:
            print(f"   ✅ Found {len(trade_logs)} trade(s) in trade_logs:")
            for trade in trade_logs:
                side, amount, price, cost_usd, order_id, created_at = trade
                print(f"      • {side.upper()} ${cost_usd:.2f} @ ${price:.8f} ({amount} tokens) - {created_at}")
        else:
            print(f"   ⚠️  No trades found in trade_logs table")
        
        # Check bot_trades table (DEX trades)
        print(f"\n   Checking bot_trades table...")
        bot_trades = db.execute(text("""
            SELECT side, value_usd, tx_signature, status, created_at
            FROM bot_trades
            WHERE bot_id = :bot_id
            ORDER BY created_at DESC
            LIMIT 10
        """), {"bot_id": bot_id}).fetchall()
        
        if bot_trades:
            print(f"   ✅ Found {len(bot_trades)} trade(s) in bot_trades:")
            for trade in bot_trades:
                side, value_usd, tx_signature, status, created_at = trade
                print(f"      • {side.upper()} ${value_usd} - {status} - {created_at}")
        else:
            print(f"   ⚠️  No trades found in bot_trades table")
        
        # Check stats
        if stats:
            print(f"\n   Stats: {stats}")
        
        print("\n" + "="*60 + "\n")
    
    # Summary
    print("📈 Summary:")
    total_trades = sum(len(db.execute(text("""
        SELECT COUNT(*) FROM trade_logs WHERE bot_id = :bot_id
    """), {"bot_id": bot[0]}).scalar() or 0) for bot in bot_result)
    
    print(f"   Total trades found: {total_trades}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
