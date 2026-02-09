#!/usr/bin/env python3
"""
Start SHARP-VB-Coinstore bot via API endpoint.
"""
import os
import sys
import requests
import json

# Get API base URL from environment or use default
API_BASE_URL = os.getenv("API_BASE_URL", "https://trading-bridge-production.up.railway.app")

print("🔍 Finding SHARP-VB-Coinstore bot via API...")
print("=" * 60)

try:
    # Step 1: List all bots to find SHARP-VB-Coinstore
    print("Step 1: Fetching bot list...")
    response = requests.get(
        f"{API_BASE_URL}/bots",
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch bots: HTTP {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        sys.exit(1)
    
    bots_data = response.json()
    bots = bots_data.get("bots", [])
    
    print(f"✅ Found {len(bots)} bot(s)")
    
    # Find SHARP-VB-Coinstore
    target_bot = None
    for bot in bots:
        if bot.get("name") == "SHARP-VB-Coinstore":
            target_bot = bot
            break
    
    if not target_bot:
        print("❌ Bot 'SHARP-VB-Coinstore' not found")
        print("\nFound bots with 'Coinstore' or 'Sharp' in name:")
        for bot in bots:
            name = bot.get("name", "")
            if "coinstore" in name.lower() or "sharp" in name.lower():
                print(f"  - {name} (ID: {bot.get('id')}, Status: {bot.get('status')})")
        sys.exit(1)
    
    bot_id = target_bot.get("id")
    bot_name = target_bot.get("name")
    current_status = target_bot.get("status")
    
    print(f"✅ Found bot:")
    print(f"   ID: {bot_id}")
    print(f"   Name: {bot_name}")
    print(f"   Current Status: {current_status}")
    print()
    
    if current_status == "running":
        print("⚠️  Bot is already running!")
        print("   No action needed.")
        sys.exit(0)
    
    # Step 2: Start the bot
    print("Step 2: Starting bot...")
    start_response = requests.post(
        f"{API_BASE_URL}/bots/{bot_id}/start",
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if start_response.status_code == 200:
        result = start_response.json()
        print(f"✅ Bot '{bot_name}' started successfully!")
        print(f"   Response: {json.dumps(result, indent=2)}")
        print()
        print("📋 Next steps:")
        print("   1. Wait ~30 seconds for bot runner to pick it up")
        print("   2. Check Railway logs for bot initialization")
        print("   3. Go to client dashboard and click 'Retry' on balance display")
        print("   4. Verify logs show: 'Coinstore API POST /spot/accountList response status=200'")
    elif start_response.status_code == 401:
        print("❌ Authentication required")
        print("   The API endpoint requires authentication.")
        print("   Please start the bot manually via:")
        print("   - Dashboard UI, or")
        print("   - SQL: UPDATE bots SET status = 'running' WHERE name = 'SHARP-VB-Coinstore';")
        sys.exit(1)
    else:
        print(f"❌ Failed to start bot: HTTP {start_response.status_code}")
        print(f"   Response: {start_response.text[:500]}")
        sys.exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"❌ Network error: {e}")
    print("\nTrying alternative method: Direct SQL update")
    print("Please run this SQL command manually:")
    print("  UPDATE bots SET status = 'running' WHERE name = 'SHARP-VB-Coinstore';")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
