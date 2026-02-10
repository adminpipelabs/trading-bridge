#!/usr/bin/env python3
"""Quick script to verify both volume and spread bot configurations via API"""
import requests
import json
import os

API_BASE = os.getenv("TRADING_BRIDGE_URL", "https://trading-bridge-production.up.railway.app")

# Expected configurations
EXPECTED_VOLUME_BOT = {
    "daily_volume_usd": 5000,
    "min_trade_usd": 10,
    "max_trade_usd": 15,
    "interval_min_seconds": 900,
    "interval_max_seconds": 1500,
    "slippage_bps": 50
}

EXPECTED_SPREAD_BOT = {
    "spread_bps": 30,
    "order_size_usd": 10,
    "refresh_seconds": 30,
    "order_expiry_seconds": 3600,
    "slippage_bps": 50
}

def verify_bot_config(bot_name, expected_config, actual_config):
    """Verify bot configuration matches expected values"""
    print(f"\n{'='*60}")
    print(f"📋 Verifying: {bot_name}")
    print(f"{'='*60}")
    
    all_match = True
    for key, expected_value in expected_config.items():
        actual_value = actual_config.get(key)
        match = "✅" if actual_value == expected_value else "❌"
        print(f"   {match} {key}: {actual_value} (expected: {expected_value})")
        if actual_value != expected_value:
            all_match = False
    
    # Show any extra config keys
    extra_keys = set(actual_config.keys()) - set(expected_config.keys())
    if extra_keys:
        print(f"\n   Additional config keys: {', '.join(extra_keys)}")
    
    return all_match

try:
    # Get all bots
    print(f"🔍 Fetching bots from {API_BASE}...")
    response = requests.get(f"{API_BASE}/bots?include_balances=false", timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch bots: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
    
    bots = response.json().get("bots", [])
    print(f"✅ Found {len(bots)} bots")
    
    # Find volume bot
    volume_bot = None
    spread_bot = None
    
    for bot in bots:
        name = bot.get("name", "")
        if "Volume Bot" in name and "Coinstore" in name:
            volume_bot = bot
        elif "Spread Bot" in name and "Coinstore" in name:
            spread_bot = bot
    
    # Verify Volume Bot
    if volume_bot:
        print(f"\n✅ Found Volume Bot:")
        print(f"   ID: {volume_bot.get('id')}")
        print(f"   Name: {volume_bot.get('name')}")
        print(f"   Status: {volume_bot.get('status')}")
        config = volume_bot.get("config", {})
        volume_match = verify_bot_config("Volume Bot", EXPECTED_VOLUME_BOT, config)
    else:
        print("\n❌ Volume Bot not found!")
        volume_match = False
    
    # Verify Spread Bot
    if spread_bot:
        print(f"\n✅ Found Spread Bot:")
        print(f"   ID: {spread_bot.get('id')}")
        print(f"   Name: {spread_bot.get('name')}")
        print(f"   Status: {spread_bot.get('status')}")
        config = spread_bot.get("config", {})
        spread_match = verify_bot_config("Spread Bot", EXPECTED_SPREAD_BOT, config)
    else:
        print("\n❌ Spread Bot not found!")
        spread_match = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    print(f"   Volume Bot: {'✅ CONFIGURED CORRECTLY' if volume_match else '❌ MISMATCH'}")
    print(f"   Spread Bot: {'✅ CONFIGURED CORRECTLY' if spread_match else '❌ MISMATCH'}")
    
    if volume_match and spread_match:
        print(f"\n✅ Both bots are configured correctly!")
        exit(0)
    else:
        print(f"\n⚠️  Some configurations don't match!")
        exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
