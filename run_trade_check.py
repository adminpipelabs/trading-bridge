#!/usr/bin/env python3
"""Run trade check query and generate dev summary"""
import os
import sys
from datetime import datetime
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
    print("🔍 Checking Volume Bot trades...\n")
    
    # Run the combined query
    result = db.execute(text("""
        SELECT 
            b.id as bot_id,
            b.name as bot_name,
            b.status as bot_status,
            b.health_status,
            b.health_message,
            b.last_trade_time as bot_last_trade_time,
            COUNT(tl.id) as trade_count,
            COALESCE(SUM(tl.cost_usd), 0) as total_volume_usd,
            COALESCE(SUM(CASE WHEN tl.side = 'buy' THEN tl.cost_usd ELSE 0 END), 0) as buy_volume,
            COALESCE(SUM(CASE WHEN tl.side = 'sell' THEN tl.cost_usd ELSE 0 END), 0) as sell_volume,
            COUNT(CASE WHEN tl.side = 'buy' THEN 1 END) as buy_count,
            COUNT(CASE WHEN tl.side = 'sell' THEN 1 END) as sell_count,
            COALESCE(AVG(tl.cost_usd), 0) as avg_trade_size,
            MAX(tl.created_at) as last_trade_time_from_logs,
            CASE 
                WHEN MAX(tl.created_at) IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (NOW() - MAX(tl.created_at)))/60
                ELSE NULL
            END as minutes_since_last_trade
        FROM bots b
        LEFT JOIN trade_logs tl ON tl.bot_id = b.id
        WHERE b.name LIKE '%Volume Bot%Coinstore%'
        GROUP BY b.id, b.name, b.status, b.health_status, b.health_message, b.last_trade_time
        ORDER BY b.updated_at DESC
        LIMIT 1
    """)).first()
    
    if not result:
        print("❌ Volume Bot not found!")
        sys.exit(1)
    
    # Get recent trades
    bot_id = result.bot_id
    recent_trades = db.execute(text("""
        SELECT 
            side,
            amount,
            price,
            cost_usd,
            order_id,
            created_at,
            EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_ago
        FROM trade_logs
        WHERE bot_id = :bot_id
        ORDER BY created_at DESC
        LIMIT 10
    """), {"bot_id": bot_id}).fetchall()
    
    # Generate summary
    print("="*70)
    print("TRADE DATA CHECK SUMMARY")
    print("="*70)
    print(f"\nBot: {result.bot_name}")
    print(f"Bot ID: {result.bot_id}")
    print(f"Status: {result.bot_status}")
    print(f"Health Status: {result.health_status}")
    print(f"Health Message: {result.health_message}")
    print(f"\nTrade Statistics:")
    print(f"  Total Trades: {result.trade_count}")
    print(f"  Total Volume: ${result.total_volume_usd:.2f}")
    print(f"  Buy Volume: ${result.buy_volume:.2f} ({result.buy_count} trades)")
    print(f"  Sell Volume: ${result.sell_volume:.2f} ({result.sell_count} trades)")
    print(f"  Avg Trade Size: ${result.avg_trade_size:.2f}")
    
    if result.last_trade_time_from_logs:
        print(f"  Last Trade: {result.last_trade_time_from_logs}")
        print(f"  Minutes Since Last Trade: {result.minutes_since_last_trade:.1f}")
    else:
        print(f"  Last Trade: None (no trades logged)")
    
    if recent_trades:
        print(f"\nRecent Trades (last {len(recent_trades)}):")
        for i, trade in enumerate(recent_trades, 1):
            print(f"  {i}. {trade.side.upper()} ${trade.cost_usd:.2f} @ ${trade.price:.6f} ({trade.minutes_ago:.1f} min ago)")
    
    # Check table existence
    table_exists = db.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'trade_logs'
        )
    """)).scalar()
    
    print(f"\nDatabase Status:")
    print(f"  trade_logs table exists: {table_exists}")
    
    # Generate dev summary
    print("\n" + "="*70)
    print("SUMMARY FOR DEV")
    print("="*70)
    
    if result.trade_count > 0:
        print("\n✅ TRADES ARE BEING LOGGED")
        print(f"   - {result.trade_count} trade(s) found in trade_logs table")
        print(f"   - Total volume: ${result.total_volume_usd:.2f}")
        print(f"   - Last trade: {result.last_trade_time_from_logs}")
        print(f"   - Data is being stored correctly")
    else:
        print("\n⚠️  NO TRADES FOUND IN trade_logs TABLE")
        print(f"   - Bot status: {result.bot_status}")
        print(f"   - Health status: {result.health_status}")
        print(f"   - Health message: {result.health_message}")
        print(f"   - Possible reasons:")
        print(f"     1. Bot hasn't executed trades yet (waiting for interval)")
        print(f"     2. Bot runner not logging trades")
        print(f"     3. Trade execution failing silently")
        print(f"     4. trade_logs table insert failing")
    
    if not table_exists:
        print("\n❌ CRITICAL: trade_logs table does not exist!")
        print("   - Run migration: migrations/add_cex_volume_bot.sql")
    
    print("\n" + "="*70)
    
    # Write summary to file
    summary_file = "TRADE_CHECK_SUMMARY_FOR_DEV.md"
    with open(summary_file, "w") as f:
        f.write(f"# Trade Data Check Summary - For Dev\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Bot:** {result.bot_name}\n")
        f.write(f"**Bot ID:** {result.bot_id}\n\n")
        f.write("---\n\n")
        f.write("## Current Status\n\n")
        f.write(f"- **Bot Status:** {result.bot_status}\n")
        f.write(f"- **Health Status:** {result.health_status}\n")
        f.write(f"- **Health Message:** {result.health_message}\n")
        f.write(f"- **Total Trades:** {result.trade_count}\n")
        f.write(f"- **Total Volume:** ${result.total_volume_usd:.2f}\n")
        f.write(f"- **Buy Trades:** {result.buy_count} (${result.buy_volume:.2f})\n")
        f.write(f"- **Sell Trades:** {result.sell_count} (${result.sell_volume:.2f})\n")
        f.write(f"- **Avg Trade Size:** ${result.avg_trade_size:.2f}\n")
        
        if result.last_trade_time_from_logs:
            f.write(f"- **Last Trade:** {result.last_trade_time_from_logs}\n")
            f.write(f"- **Minutes Since Last Trade:** {result.minutes_since_last_trade:.1f}\n")
        else:
            f.write(f"- **Last Trade:** None\n")
        
        f.write(f"\n## Database Status\n\n")
        f.write(f"- **trade_logs table exists:** {table_exists}\n")
        
        if recent_trades:
            f.write(f"\n## Recent Trades\n\n")
            for i, trade in enumerate(recent_trades, 1):
                f.write(f"{i}. **{trade.side.upper()}** ${trade.cost_usd:.2f} @ ${trade.price:.6f} ({trade.minutes_ago:.1f} min ago)\n")
        
        f.write(f"\n## Conclusion\n\n")
        if result.trade_count > 0:
            f.write("✅ **TRADES ARE BEING LOGGED CORRECTLY**\n\n")
            f.write("The volume bot is executing trades and data is being stored in the `trade_logs` table.\n")
            f.write("Data is available for reporting and AI assistance via:\n")
            f.write("- API endpoint: `GET /bots/{bot_id}/trades-history`\n")
            f.write("- Direct SQL query: `SELECT * FROM trade_logs WHERE bot_id = '{bot_id}'`\n")
        else:
            f.write("⚠️  **NO TRADES FOUND**\n\n")
            f.write("The bot is running but no trades have been logged to the `trade_logs` table.\n\n")
            f.write("**Next Steps:**\n")
            f.write("1. Check Hetzner logs: `journalctl -u trading-bridge -f | grep 'market order'`\n")
            f.write("2. Verify bot runner is executing trades\n")
            f.write("3. Check if trade_logs table insert is failing\n")
            f.write("4. Verify bot configuration (intervals, trade sizes)\n")
    
    print(f"\n✅ Summary written to: {summary_file}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
