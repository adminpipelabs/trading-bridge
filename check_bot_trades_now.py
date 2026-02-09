#!/usr/bin/env python3
"""
Quick script to check Sharp's BitMart volume bot trades.
Uses the new API endpoints.
"""
import requests
import json
import sys

# API base URL
API_BASE = "https://trading-bridge-production.up.railway.app"

def find_sharp_bot():
    """Find Sharp's BitMart volume bot ID"""
    print("🔍 Finding Sharp's BitMart volume bot...\n")
    
    try:
        response = requests.get(f"{API_BASE}/bots")
        response.raise_for_status()
        bots = response.json()
        
        # Find Sharp's volume bot
        sharp_bot = None
        for bot in bots:
            account = bot.get("account", "")
            bot_type = bot.get("bot_type", "")
            name = bot.get("name", "").lower()
            
            if account == "client_new_sharp_foundation" and bot_type == "volume":
                if "bitmart" in name or bot.get("exchange") == "bitmart":
                    sharp_bot = bot
                    break
        
        if not sharp_bot:
            print("❌ No BitMart volume bot found for Sharp")
            print("\nAvailable bots for this account:")
            for bot in bots:
                if bot.get("account") == "client_new_sharp_foundation":
                    print(f"  - {bot.get('name')} ({bot.get('bot_type')}, exchange: {bot.get('exchange')})")
            return None
        
        return sharp_bot
        
    except Exception as e:
        print(f"❌ Error finding bot: {e}")
        return None

def check_trades(bot_id):
    """Check trades for a bot"""
    print(f"📊 Checking trades for bot: {bot_id}\n")
    
    try:
        # Get trades endpoint
        response = requests.get(f"{API_BASE}/bots/{bot_id}/trades?limit=50")
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except Exception as e:
        print(f"❌ Error checking trades: {e}")
        return None

def check_stats(bot_id):
    """Check bot stats (includes trades)"""
    try:
        response = requests.get(f"{API_BASE}/bots/{bot_id}/stats")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error checking stats: {e}")
        return None

def main():
    print("="*60)
    print("CHECKING SHARP'S BITMART VOLUME BOT TRADES")
    print("="*60)
    print()
    
    # Step 1: Find bot
    bot = find_sharp_bot()
    if not bot:
        sys.exit(1)
    
    bot_id = bot["id"]
    bot_name = bot.get("name", "Unknown")
    bot_status = bot.get("status", "unknown")
    
    print(f"✅ Found bot:")
    print(f"   Name: {bot_name}")
    print(f"   ID: {bot_id}")
    print(f"   Status: {bot_status}")
    print(f"   Exchange: {bot.get('exchange', 'N/A')}")
    print()
    
    # Step 2: Check trades
    trades_data = check_trades(bot_id)
    
    if not trades_data:
        print("❌ Could not fetch trades data")
        sys.exit(1)
    
    # Display results
    print("="*60)
    print("TRADE RESULTS")
    print("="*60)
    print()
    
    total_trades = trades_data.get("total_trades", 0)
    total_volume = trades_data.get("total_volume_usd", 0)
    buy_count = trades_data.get("buy_count", 0)
    sell_count = trades_data.get("sell_count", 0)
    trades = trades_data.get("trades", [])
    
    print(f"📈 Summary:")
    print(f"   Total Trades: {total_trades}")
    print(f"   Total Volume: ${total_volume:.2f}")
    print(f"   Buy Orders: {buy_count}")
    print(f"   Sell Orders: {sell_count}")
    print()
    
    if total_trades == 0:
        print("❌ NO TRADES FOUND")
        print()
        print("Possible reasons:")
        print("  1. Bot just started (trades happen every 15-45 minutes)")
        print("  2. Bot doesn't have enough balance")
        print("  3. Bot is not running (status: {})".format(bot_status))
        print("  4. API keys are invalid")
        print("  5. Exchange API errors")
        print()
        print("Check Railway logs for more details:")
        print("  https://railway.app/dashboard")
    else:
        print(f"✅ Found {total_trades} trade(s):\n")
        
        # Show recent trades
        for i, trade in enumerate(trades[:10], 1):  # Show first 10
            side = trade.get("side", "unknown").upper()
            amount = trade.get("amount")
            price = trade.get("price")
            value_usd = trade.get("value_usd", 0)
            created_at = trade.get("created_at", "")
            source = trade.get("source", "unknown")
            order_id = trade.get("order_id") or trade.get("tx_signature", "N/A")
            
            print(f"  {i}. {side} Trade")
            if amount:
                print(f"     Amount: {amount:,.2f} tokens")
            if price:
                print(f"     Price: ${price:.8f}")
            print(f"     Value: ${value_usd:.2f}")
            print(f"     Order ID: {order_id}")
            print(f"     Time: {created_at}")
            print(f"     Source: {source}")
            print()
        
        if len(trades) > 10:
            print(f"  ... and {len(trades) - 10} more trades")
            print()
    
    # Also show stats
    print("="*60)
    print("BOT HEALTH STATUS")
    print("="*60)
    print()
    
    stats_data = check_stats(bot_id)
    if stats_data:
        health_status = stats_data.get("health_status", "unknown")
        health_message = stats_data.get("health_message", "N/A")
        last_trade_time = stats_data.get("last_trade_time")
        
        print(f"   Health Status: {health_status}")
        print(f"   Health Message: {health_message}")
        print(f"   Last Trade Time: {last_trade_time or 'Never'}")
        print()
    
    print("="*60)
    print("API Endpoints Used:")
    print(f"  GET {API_BASE}/bots/{bot_id}/trades")
    print(f"  GET {API_BASE}/bots/{bot_id}/stats")
    print("="*60)

if __name__ == "__main__":
    main()
