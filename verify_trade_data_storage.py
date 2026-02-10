#!/usr/bin/env python3
"""Verify trade data is being stored - Check trade_logs table"""
import os
import sys
from datetime import datetime, timedelta

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("⚠️  DATABASE_URL not set")
    print("\nTo check trade data:")
    print("1. Query Railway PostgreSQL:")
    print("   SELECT * FROM trade_logs WHERE bot_id = '<bot_id>' ORDER BY created_at DESC LIMIT 10;")
    print("\n2. Use API endpoint:")
    print("   GET /bots/{bot_id}/trades-history")
    sys.exit(1)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    print("🔍 Checking trade data storage...\n")
    
    # 1. Check if trade_logs table exists
    table_exists = db.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'trade_logs'
        )
    """)).scalar()
    
    if not table_exists:
        print("❌ trade_logs table does not exist!")
        print("\nRun migration:")
        print("  psql $DATABASE_URL < migrations/add_cex_volume_bot.sql")
        sys.exit(1)
    
    print("✅ trade_logs table exists\n")
    
    # 2. Find volume bot
    bot_result = db.execute(text("""
        SELECT id, name, status, exchange
        FROM bots
        WHERE name LIKE '%Volume Bot%Coinstore%'
        ORDER BY updated_at DESC
        LIMIT 1
    """)).first()
    
    if not bot_result:
        print("❌ Volume bot not found!")
        sys.exit(1)
    
    bot_id = bot_result.id
    bot_name = bot_result.name
    status = bot_result.status
    
    print(f"✅ Found bot: {bot_name}")
    print(f"   Bot ID: {bot_id}")
    print(f"   Status: {status}\n")
    
    # 3. Check trade count
    trade_count = db.execute(text("""
        SELECT COUNT(*) as count
        FROM trade_logs
        WHERE bot_id = :bot_id
    """), {"bot_id": bot_id}).scalar()
    
    print(f"📊 Trade Statistics:")
    print(f"   Total Trades: {trade_count}")
    
    if trade_count == 0:
        print("\n⚠️  No trades found in trade_logs table")
        print("\nPossible reasons:")
        print("  1. Bot hasn't executed trades yet (waiting for interval)")
        print("  2. Bot runner not logging trades")
        print("  3. Trade execution failing silently")
        print("\nCheck Hetzner logs:")
        print("  journalctl -u trading-bridge -f | grep 'market order'")
    else:
        # Get recent trades
        recent_trades = db.execute(text("""
            SELECT side, amount, price, cost_usd, created_at
            FROM trade_logs
            WHERE bot_id = :bot_id
            ORDER BY created_at DESC
            LIMIT 5
        """), {"bot_id": bot_id}).fetchall()
        
        print(f"\n📋 Recent Trades (last 5):")
        for i, trade in enumerate(recent_trades, 1):
            time_ago = (datetime.now() - trade.created_at).total_seconds() / 60 if trade.created_at else None
            time_str = f" ({time_ago:.1f} min ago)" if time_ago else ""
            print(f"   {i}. {trade.side.upper()} ${trade.cost_usd:.2f} @ ${trade.price:.6f}{time_str}")
        
        # Get volume stats
        stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(cost_usd) as total_volume,
                SUM(CASE WHEN side = 'buy' THEN cost_usd ELSE 0 END) as buy_volume,
                SUM(CASE WHEN side = 'sell' THEN cost_usd ELSE 0 END) as sell_volume,
                AVG(cost_usd) as avg_trade_size,
                MAX(created_at) as last_trade
            FROM trade_logs
            WHERE bot_id = :bot_id
        """), {"bot_id": bot_id}).first()
        
        print(f"\n💰 Volume Statistics:")
        print(f"   Total Volume: ${stats.total_volume:.2f}")
        print(f"   Buy Volume: ${stats.buy_volume:.2f}")
        print(f"   Sell Volume: ${stats.sell_volume:.2f}")
        print(f"   Avg Trade Size: ${stats.avg_trade_size:.2f}")
        print(f"   Last Trade: {stats.last_trade}")
        
        if stats.last_trade:
            time_since = (datetime.now() - stats.last_trade).total_seconds() / 60
            print(f"   Time Since Last Trade: {time_since:.1f} minutes")
    
    print("\n✅ Trade data storage verified!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
