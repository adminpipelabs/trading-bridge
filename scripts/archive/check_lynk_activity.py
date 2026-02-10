#!/usr/bin/env python3
"""
Check activity for Real Lynk client account.
Shows bots, trades, wallet status, and recent activity.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

# Fix Railway postgres:// URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

def check_lynk_activity():
    """Check all activity for Lynk client"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("REAL LYNK ACCOUNT ACTIVITY CHECK")
        print("=" * 60)
        print()
        
        # 1. Find Lynk client
        print("1️⃣  Finding Lynk client...")
        client_result = db.execute(text("""
            SELECT id, name, account_identifier, wallet_address, status, created_at
            FROM clients
            WHERE LOWER(name) LIKE '%lynk%' OR account_identifier LIKE '%lynk%'
            ORDER BY created_at DESC
        """))
        clients = client_result.fetchall()
        
        if not clients:
            print("   ❌ No Lynk client found")
            return
        
        for client in clients:
            client_id = client[0]
            client_name = client[1]
            account_id = client[2]
            wallet_addr = client[3]
            status = client[4]
            created = client[5]
            
            print(f"   ✅ Found: {client_name}")
            print(f"      ID: {client_id}")
            print(f"      Account: {account_id}")
            print(f"      Wallet: {wallet_addr}")
            print(f"      Status: {status}")
            print(f"      Created: {created}")
            print()
            
            # 2. Check wallets
            print("2️⃣  Checking wallets...")
            wallets_result = db.execute(text("""
                SELECT id, chain, address, created_at
                FROM wallets
                WHERE client_id = :client_id
            """), {"client_id": client_id})
            wallets = wallets_result.fetchall()
            
            if wallets:
                for wallet in wallets:
                    print(f"   ✅ Wallet: {wallet[2]} ({wallet[1]}) - Created: {wallet[3]}")
            else:
                print("   ⚠️  No wallets found")
            print()
            
            # 3. Check trading keys
            print("3️⃣  Checking trading keys...")
            keys_result = db.execute(text("""
                SELECT id, chain, wallet_address, added_by, created_at
                FROM trading_keys
                WHERE client_id = :client_id
            """), {"client_id": client_id})
            keys = keys_result.fetchall()
            
            if keys:
                for key in keys:
                    print(f"   ✅ Key: {key[2]} ({key[1]}) - Added by: {key[3]} - Created: {key[4]}")
            else:
                print("   ⚠️  No trading keys found")
            print()
            
            # 4. Check bots
            print("4️⃣  Checking bots...")
            bots_result = db.execute(text("""
                SELECT id, name, bot_type, connector, pair, status, health_status, 
                       health_message, last_trade_time, created_at, updated_at,
                       config->>'daily_volume_usd' as daily_target,
                       stats->>'trades_today' as trades_today,
                       stats->>'volume_today' as volume_today
                FROM bots
                WHERE client_id = :client_id OR account = :account_id
                ORDER BY created_at DESC
            """), {"client_id": client_id, "account_id": account_id})
            bots = bots_result.fetchall()
            
            if bots:
                for bot in bots:
                    bot_id = bot[0]
                    bot_name = bot[1]
                    bot_type = bot[2] or 'N/A'
                    connector = bot[3]
                    pair = bot[4]
                    status = bot[5]
                    health = bot[6] or 'unknown'
                    health_msg = bot[7] or ''
                    last_trade = bot[8]
                    created = bot[9]
                    updated = bot[10]
                    daily_target = bot[11] or 'N/A'
                    trades_today = bot[12] or '0'
                    volume_today = bot[13] or '0'
                    
                    print(f"   ✅ Bot: {bot_name}")
                    print(f"      ID: {bot_id}")
                    print(f"      Type: {bot_type}")
                    print(f"      Connector: {connector}")
                    print(f"      Pair: {pair}")
                    print(f"      Status: {status}")
                    print(f"      Health: {health} - {health_msg}")
                    print(f"      Last Trade: {last_trade or 'Never'}")
                    print(f"      Daily Target: ${daily_target}")
                    print(f"      Trades Today: {trades_today}")
                    print(f"      Volume Today: ${volume_today}")
                    print(f"      Created: {created}")
                    print(f"      Updated: {updated}")
                    print()
                    
                    # Check bot trades
                    trades_result = db.execute(text("""
                        SELECT COUNT(*) as count, 
                               MAX(created_at) as last_trade,
                               SUM(CAST(value_usd AS NUMERIC)) as total_volume
                        FROM bot_trades
                        WHERE bot_id = :bot_id
                    """), {"bot_id": bot_id})
                    trade_stats = trades_result.fetchone()
                    
                    if trade_stats and trade_stats[0] > 0:
                        print(f"      📊 Trade Stats:")
                        print(f"         Total Trades: {trade_stats[0]}")
                        print(f"         Last Trade: {trade_stats[1]}")
                        print(f"         Total Volume: ${trade_stats[2] or 0}")
                        
                        # Recent trades
                        recent_trades_result = db.execute(text("""
                            SELECT side, amount, price, value_usd, status, created_at
                            FROM bot_trades
                            WHERE bot_id = :bot_id
                            ORDER BY created_at DESC
                            LIMIT 5
                        """), {"bot_id": bot_id})
                        recent_trades = recent_trades_result.fetchall()
                        
                        if recent_trades:
                            print(f"      📈 Recent Trades (last 5):")
                            for trade in recent_trades:
                                print(f"         {trade[0].upper()} {trade[1]} @ ${trade[2]} = ${trade[3]} ({trade[4]}) - {trade[5]}")
                    else:
                        print(f"      ⚠️  No trades recorded in database")
                    print()
            else:
                print("   ⚠️  No bots found")
            print()
            
            # 5. Check connectors
            print("5️⃣  Checking connectors...")
            connectors_result = db.execute(text("""
                SELECT id, name, created_at
                FROM connectors
                WHERE client_id = :client_id
            """), {"client_id": client_id})
            connectors = connectors_result.fetchall()
            
            if connectors:
                for conn in connectors:
                    print(f"   ✅ Connector: {conn[1]} - Created: {conn[2]}")
            else:
                print("   ⚠️  No connectors found")
            print()
            
            # 6. Check health logs (last 24 hours)
            print("6️⃣  Checking health logs (last 24h)...")
            health_logs_result = db.execute(text("""
                SELECT checked_at, health_status, reason, trade_count_since_last, last_trade_found
                FROM bot_health_logs
                WHERE bot_id IN (
                    SELECT id FROM bots WHERE client_id = :client_id OR account = :account_id
                )
                AND checked_at > NOW() - INTERVAL '24 hours'
                ORDER BY checked_at DESC
                LIMIT 10
            """), {"client_id": client_id, "account_id": account_id})
            health_logs = health_logs_result.fetchall()
            
            if health_logs:
                for log in health_logs:
                    print(f"   📋 {log[0]}: {log[1]} - {log[2]}")
                    if log[3]:
                        print(f"      Trades since last check: {log[3]}")
                    if log[4]:
                        print(f"      Last trade found: {log[4]}")
            else:
                print("   ⚠️  No health logs in last 24h")
            print()
            
            print("=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Client: {client_name}")
            print(f"Wallets: {len(wallets)}")
            print(f"Trading Keys: {len(keys)}")
            print(f"Bots: {len(bots)}")
            print(f"Connectors: {len(connectors)}")
            print(f"Health Checks (24h): {len(health_logs)}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_lynk_activity()
