#!/usr/bin/env python3
"""Check trades via API endpoint"""
import requests
import json
import os
import sys

API_BASE = os.getenv("TRADING_BRIDGE_URL", "https://trading-bridge-production.up.railway.app")

def get_bot_id_by_name(name_pattern):
    """Get bot ID by name pattern"""
    try:
        # Try to get bots - this might require auth
        response = requests.get(f"{API_BASE}/bots?include_balances=false", timeout=10)
        if response.status_code == 200:
            bots = response.json().get("bots", [])
            for bot in bots:
                if name_pattern.lower() in bot.get("name", "").lower():
                    return bot.get("id"), bot.get("name")
        return None, None
    except Exception as e:
        print(f"⚠️  Could not fetch bots via API: {e}")
        return None, None

def check_trades_via_api(bot_id):
    """Check trades for a bot via API"""
    try:
        response = requests.get(f"{API_BASE}/bots/{bot_id}/trades-history", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"❌ API returned {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return None

def main():
    print("🔍 Checking trades for Volume Bot...\n")
    
    # Try to find bot ID
    bot_id, bot_name = get_bot_id_by_name("Volume Bot Coinstore")
    
    if not bot_id:
        print("❌ Could not find bot via API (may require authentication)")
        print("\n📋 Alternative: Check directly via database:")
        print("""
# Connect to Railway PostgreSQL and run:
SELECT 
    b.id,
    b.name,
    b.status,
    COUNT(tl.id) as trade_count,
    SUM(tl.cost_usd) as total_volume,
    MAX(tl.created_at) as last_trade
FROM bots b
LEFT JOIN trade_logs tl ON tl.bot_id = b.id
WHERE b.name LIKE '%Volume Bot%Coinstore%'
GROUP BY b.id, b.name, b.status;
        """)
        sys.exit(1)
    
    print(f"✅ Found bot: {bot_name}")
    print(f"   Bot ID: {bot_id}\n")
    
    # Check trades
    trades_data = check_trades_via_api(bot_id)
    
    if trades_data:
        trades = trades_data.get("trades", [])
        total_volume = trades_data.get("total_volume", 0)
        buy_count = trades_data.get("buy_count", 0)
        sell_count = trades_data.get("sell_count", 0)
        last_trade_time = trades_data.get("last_trade_time")
        
        print(f"📊 Trade Statistics:")
        print(f"   Total Trades: {len(trades)}")
        print(f"   Buy Trades: {buy_count}")
        print(f"   Sell Trades: {sell_count}")
        print(f"   Total Volume: ${total_volume:.2f}")
        print(f"   Last Trade: {last_trade_time}\n")
        
        if trades:
            print(f"📋 Recent Trades (last 5):")
            for i, trade in enumerate(trades[:5], 1):
                side = trade.get("side", "").upper()
                value = trade.get("value_usd", 0)
                price = trade.get("price", 0)
                created_at = trade.get("created_at", "")
                print(f"   {i}. {side} ${value:.2f} @ ${price:.6f} - {created_at}")
            
            print("\n✅ Trades are being logged!")
        else:
            print("⚠️  No trades found")
            print("\nPossible reasons:")
            print("  1. Bot hasn't executed trades yet")
            print("  2. Bot is waiting for interval (15-25 min)")
            print("  3. Check Hetzner logs for errors")
    else:
        print("❌ Could not fetch trade data via API")
        print("\nCheck directly via database query (see above)")

if __name__ == "__main__":
    main()
