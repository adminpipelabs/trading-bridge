#!/usr/bin/env python3
"""Quick check if volume bot has executed trades - 15 min check"""
import os
import sys
from datetime import datetime, timedelta

# Try to use database if available, otherwise use API
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Database method
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        print("🔍 Checking Volume Bot trades (15 min check)...\n")
        
        # Find the Coinstore volume bot
        bot_result = db.execute(text("""
            SELECT id, name, status, config, updated_at, health_status, last_trade_time
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
        health_status = bot_result.health_status
        last_trade_time = bot_result.last_trade_time
        
        print(f"✅ Found bot: {bot_name}")
        print(f"   Bot ID: {bot_id}")
        print(f"   Status: {status}")
        print(f"   Health: {health_status}")
        print(f"   Last Trade Time: {last_trade_time}\n")
        
        # Check trade_logs
        trades = db.execute(text("""
            SELECT side, amount, price, cost_usd, created_at
            FROM trade_logs
            WHERE bot_id = :bot_id
            ORDER BY created_at DESC
            LIMIT 10
        """), {"bot_id": bot_id}).fetchall()
        
        if trades:
            print(f"✅ Found {len(trades)} trade(s):\n")
            total_volume = 0
            for i, trade in enumerate(trades, 1):
                total_volume += float(trade.cost_usd or 0)
                time_ago = datetime.now(timezone.utc) - trade.created_at if trade.created_at else None
                time_str = f" ({time_ago.total_seconds()/60:.1f} min ago)" if time_ago else ""
                print(f"  📊 Trade #{i}: {trade.side.upper()} ${trade.cost_usd:.2f} @ ${trade.price:.6f}{time_str}")
            print(f"\n💰 Total Volume: ${total_volume:.2f}")
            
            # Check if recent trade
            latest_trade = trades[0]
            if latest_trade.created_at:
                time_since = (datetime.now(timezone.utc) - latest_trade.created_at).total_seconds() / 60
                if time_since < 20:
                    print(f"\n✅ Latest trade was {time_since:.1f} minutes ago - Bot is trading!")
                else:
                    print(f"\n⚠️  Latest trade was {time_since:.1f} minutes ago - May be waiting for interval")
        else:
            print("❌ No trades found in trade_logs table")
            print("\nPossible reasons:")
            print("  1. Bot is waiting for interval (15-25 min)")
            print("  2. Bot has an error (check health_status)")
            print("  3. Bot runner not executing trades")
            print("  4. Exchange API issue")
            
            # Check config
            config = bot_result.config or {}
            print(f"\nBot Config:")
            print(f"  Min Interval: {config.get('interval_min_seconds', 'N/A')} seconds ({config.get('interval_min_seconds', 0)/60:.1f} min)")
            print(f"  Max Interval: {config.get('interval_max_seconds', 'N/A')} seconds ({config.get('interval_max_seconds', 0)/60:.1f} min)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
else:
    print("⚠️  DATABASE_URL not set")
    print("\nTo check trades:")
    print("1. Check Hetzner logs: journalctl -u trading-bridge -f | grep 'market order'")
    print("2. Check UI - Volume should show > $0 if trades executed")
    print("3. Query database directly:")
    print("   SELECT * FROM trade_logs WHERE bot_id = '<bot_id>' ORDER BY created_at DESC LIMIT 5;")
