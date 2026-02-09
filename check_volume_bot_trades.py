#!/usr/bin/env python3
"""
Check if Sharp's BitMart volume bot has executed any trades.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    print("Set it with: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    print("🔍 Checking trades for Sharp's BitMart volume bot...\n")
    
    # Step 1: Find Sharp's volume bot
    print("Step 1: Finding Sharp's bot...")
    bot_result = db.execute(text("""
        SELECT id, name, account, bot_type, exchange, status, created_at
        FROM bots
        WHERE account = 'client_new_sharp_foundation'
        AND bot_type = 'volume'
        AND (exchange = 'bitmart' OR name ILIKE '%bitmart%')
        ORDER BY created_at DESC
        LIMIT 1
    """)).first()
    
    if not bot_result:
        print("❌ No BitMart volume bot found for Sharp")
        print("\nChecking all bots for this account:")
        all_bots = db.execute(text("""
            SELECT id, name, bot_type, exchange, status
            FROM bots
            WHERE account = 'client_new_sharp_foundation'
        """)).fetchall()
        for bot in all_bots:
            print(f"  - {bot.name} ({bot.bot_type}, exchange: {bot.exchange}, status: {bot.status})")
        sys.exit(1)
    
    bot_id = bot_result.id
    bot_name = bot_result.name
    print(f"✅ Found bot: {bot_name}")
    print(f"   Bot ID: {bot_id}")
    print(f"   Status: {bot_result.status}")
    print(f"   Exchange: {bot_result.exchange}")
    print(f"   Created: {bot_result.created_at}\n")
    
    # Step 2: Check trade_logs table (CEX bots)
    print("Step 2: Checking trade_logs table (CEX bots)...")
    try:
        trade_logs = db.execute(text("""
            SELECT id, side, amount, price, cost_usd, order_id, created_at
            FROM trade_logs
            WHERE bot_id = :bot_id
            ORDER BY created_at DESC
            LIMIT 20
        """), {"bot_id": bot_id}).fetchall()
        
        if trade_logs:
            print(f"✅ Found {len(trade_logs)} trade(s) in trade_logs table:\n")
            total_volume = 0
            for trade in trade_logs:
                total_volume += float(trade.cost_usd or 0)
                print(f"  📊 Trade #{trade.id}")
                print(f"     Side: {trade.side.upper()}")
                print(f"     Amount: {trade.amount} SHARP")
                print(f"     Price: ${trade.price}")
                print(f"     Cost: ${trade.cost_usd}")
                print(f"     Order ID: {trade.order_id}")
                print(f"     Time: {trade.created_at}")
                print()
            print(f"💰 Total Volume: ${total_volume:.2f}")
        else:
            print("❌ No trades found in trade_logs table")
    except Exception as e:
        if "does not exist" in str(e).lower():
            print("⚠️  trade_logs table doesn't exist yet")
            print("   This means no trades have been logged")
        else:
            print(f"❌ Error querying trade_logs: {e}")
    
    print()
    
    # Step 3: Check bot_trades table (DEX bots - but might have some)
    print("Step 3: Checking bot_trades table (DEX bots)...")
    try:
        bot_trades = db.execute(text("""
            SELECT id, side, amount, price, value_usd, tx_signature, status, created_at
            FROM bot_trades
            WHERE bot_id = :bot_id
            ORDER BY created_at DESC
            LIMIT 20
        """), {"bot_id": bot_id}).fetchall()
        
        if bot_trades:
            print(f"✅ Found {len(bot_trades)} trade(s) in bot_trades table:\n")
            for trade in bot_trades:
                print(f"  📊 Trade #{trade.id}")
                print(f"     Side: {trade.side}")
                print(f"     Value: ${trade.value_usd}")
                print(f"     Status: {trade.status}")
                print(f"     Time: {trade.created_at}")
                print()
        else:
            print("❌ No trades found in bot_trades table")
    except Exception as e:
        print(f"⚠️  Error querying bot_trades: {e}")
    
    print()
    
    # Step 4: Check bot stats/health
    print("Step 4: Checking bot health status...")
    bot_health = db.execute(text("""
        SELECT health_status, health_message, last_trade_time, status_updated_at
        FROM bots
        WHERE id = :bot_id
    """), {"bot_id": bot_id}).first()
    
    if bot_health:
        print(f"   Health Status: {bot_health.health_status}")
        print(f"   Health Message: {bot_health.health_message}")
        print(f"   Last Trade Time: {bot_health.last_trade_time}")
        print(f"   Status Updated: {bot_health.status_updated_at}")
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    
    trade_count = len(trade_logs) if 'trade_logs' in locals() and trade_logs else 0
    if trade_count > 0:
        print(f"✅ Bot HAS executed {trade_count} trade(s) on BitMart")
        print(f"   Check trade_logs table for details")
    else:
        print("❌ Bot has NOT executed any trades yet")
        print("\nPossible reasons:")
        print("  1. Bot just started (trades happen every 15-45 minutes)")
        print("  2. Bot doesn't have enough balance")
        print("  3. Bot is not running (check status)")
        print("  4. API keys are invalid")
        print("  5. Exchange API errors")
        print("\nCheck Railway logs for bot activity")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
