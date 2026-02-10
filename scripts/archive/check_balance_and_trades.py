#!/usr/bin/env python3
"""
Check bot balances and trades - diagnostic script
Shows what balances SHOULD be vs what's being fetched, and if trades are happening
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 80)
print("BOT BALANCE & TRADE DIAGNOSTIC")
print("=" * 80)

# Get all CEX bots
bots = db.execute(text("""
    SELECT id, name, account, connector, bot_type, pair, base_asset, quote_asset, status, health_status, health_message
    FROM bots
    WHERE bot_type IN ('volume', 'spread')
    ORDER BY name
""")).fetchall()

if not bots:
    print("❌ No CEX bots found")
    sys.exit(0)

for bot in bots:
    bot_id = bot.id
    bot_name = bot.name
    connector = bot.connector or 'unknown'
    status = bot.status
    health_status = bot.health_status
    health_message = bot.health_message
    
    print(f"\n{'='*80}")
    print(f"🤖 Bot: {bot_name}")
    print(f"   ID: {bot_id}")
    print(f"   Connector: {connector}")
    print(f"   Status: {status}")
    print(f"   Health: {health_status}")
    if health_message:
        print(f"   Message: {health_message}")
    
    # Check trades
    trades = db.execute(text("""
        SELECT COUNT(*) as count, 
               SUM(cost_usd) as total_volume,
               COUNT(CASE WHEN side = 'buy' THEN 1 END) as buys,
               COUNT(CASE WHEN side = 'sell' THEN 1 END) as sells,
               MAX(created_at) as last_trade
        FROM trade_logs
        WHERE bot_id = :bot_id
    """), {"bot_id": bot_id}).fetchone()
    
    trade_count = trades.count or 0
    total_volume = float(trades.total_volume or 0)
    buys = trades.buys or 0
    sells = trades.sells or 0
    last_trade = trades.last_trade
    
    print(f"\n📊 TRADES:")
    print(f"   Total: {trade_count}")
    print(f"   Buys: {buys}, Sells: {sells}")
    print(f"   Volume: ${total_volume:.2f}")
    if last_trade:
        print(f"   Last Trade: {last_trade}")
    else:
        print(f"   Last Trade: Never")
    
    # Check API keys
    client_id = db.execute(text("""
        SELECT client_id FROM clients WHERE account_identifier = :account
    """), {"account": bot.account}).scalar()
    
    if client_id:
        api_keys = db.execute(text("""
            SELECT exchange, created_at
            FROM exchange_credentials
            WHERE client_id = :client_id AND exchange = :exchange
        """), {"client_id": client_id, "exchange": connector.lower()}).fetchone()
        
        if api_keys:
            print(f"\n🔑 API KEYS:")
            print(f"   ✅ Found for {connector}")
            print(f"   Created: {api_keys.created_at}")
        else:
            print(f"\n🔑 API KEYS:")
            print(f"   ❌ NOT FOUND for {connector}")
            print(f"   Client ID: {client_id}")
            print(f"   Expected exchange: {connector.lower()}")
    
    # Recent trades detail
    if trade_count > 0:
        recent = db.execute(text("""
            SELECT side, amount, price, cost_usd, created_at
            FROM trade_logs
            WHERE bot_id = :bot_id
            ORDER BY created_at DESC
            LIMIT 5
        """), {"bot_id": bot_id}).fetchall()
        
        print(f"\n📈 RECENT TRADES (last 5):")
        for t in recent:
            print(f"   {t.created_at} | {t.side.upper()} | {t.amount} @ ${t.price} | ${t.cost_usd:.2f}")
    else:
        print(f"\n⚠️  NO TRADES YET")
        print(f"   Possible reasons:")
        print(f"   1. Bot just started (trades happen every 15-45 min)")
        print(f"   2. Balance fetch failing (check Railway logs)")
        print(f"   3. API keys missing/invalid")
        print(f"   4. IP whitelisting issue")
        print(f"   5. Insufficient balance on exchange")

print(f"\n{'='*80}")
print("SUMMARY:")
print("=" * 80)
print("\n✅ If trades > 0: Bot IS trading (balance fetch might still fail for UI)")
print("❌ If trades = 0: Bot is NOT trading (check Railway logs for errors)")
print("\n💡 Next steps:")
print("   1. Check Railway logs for balance fetch errors")
print("   2. Verify API keys are correct and IPs whitelisted")
print("   3. Check exchange account directly for actual balances")
print("=" * 80)

db.close()
