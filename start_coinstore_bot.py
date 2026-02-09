#!/usr/bin/env python3
"""
Start SHARP-VB-Coinstore bot programmatically.
Tries multiple methods:
1. Direct database access (if DATABASE_URL is set)
2. Railway CLI (if available)
3. API endpoint (if backend is accessible)
"""
import os
import sys
import subprocess
import json
from sqlalchemy import create_engine, text

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Try to get from Railway CLI if DATABASE_URL not set
if not DATABASE_URL:
    print("⚠️  DATABASE_URL not found, trying Railway CLI...")
    try:
        result = subprocess.run(
            ["railway", "variables", "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            vars_data = json.loads(result.stdout)
            for var in vars_data:
                if var.get("key") == "DATABASE_URL":
                    DATABASE_URL = var.get("value")
                    print("✅ Found DATABASE_URL from Railway CLI")
                    break
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass

if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    print("Options:")
    print("  1. Set it: export DATABASE_URL='postgresql://...'")
    print("  2. Use Railway CLI: railway variables")
    print("  3. Or provide it as argument: python start_coinstore_bot.py <DATABASE_URL>")
    if len(sys.argv) > 1:
        DATABASE_URL = sys.argv[1]
        print(f"✅ Using DATABASE_URL from command line argument")
    else:
        sys.exit(1)

# Convert Railway format if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(DATABASE_URL)
    
    print("🔍 Looking for SHARP-VB-Coinstore bot...")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Find the bot by name
        result = conn.execute(text("""
            SELECT id, name, bot_type, status, account, connector
            FROM bots 
            WHERE name = 'SHARP-VB-Coinstore'
            LIMIT 1
        """))
        
        bot = result.fetchone()
        
        if not bot:
            print("❌ Bot 'SHARP-VB-Coinstore' not found in database")
            print("\nChecking for similar bots...")
            similar = conn.execute(text("""
                SELECT id, name, bot_type, status
                FROM bots 
                WHERE name ILIKE '%coinstore%' OR name ILIKE '%sharp%'
                ORDER BY name
            """))
            print("\nFound similar bots:")
            for row in similar:
                print(f"  - {row.name} (ID: {row.id}, Type: {row.bot_type}, Status: {row.status})")
            sys.exit(1)
        
        bot_id, bot_name, bot_type, current_status, account, connector = bot
        
        print(f"✅ Found bot:")
        print(f"   ID: {bot_id}")
        print(f"   Name: {bot_name}")
        print(f"   Type: {bot_type}")
        print(f"   Account: {account}")
        print(f"   Connector: {connector}")
        print(f"   Current Status: {current_status}")
        print()
        
        if current_status == 'running':
            print("⚠️  Bot is already running!")
            print("   No action needed.")
            sys.exit(0)
        
        # Update status to running
        print(f"🚀 Starting bot...")
        conn.execute(text("""
            UPDATE bots 
            SET status = 'running', error = NULL
            WHERE id = :bot_id
        """), {"bot_id": bot_id})
        
        conn.commit()
        
        # Verify the update
        verify = conn.execute(text("""
            SELECT status FROM bots WHERE id = :bot_id
        """), {"bot_id": bot_id}).fetchone()
        
        if verify and verify[0] == 'running':
            print(f"✅ Bot '{bot_name}' started successfully!")
            print(f"   Status updated to: running")
            print()
            print("📋 Next steps:")
            print("   1. Wait ~30 seconds for bot runner to pick it up")
            print("   2. Check Railway logs for bot initialization")
            print("   3. Go to client dashboard and click 'Retry' on balance display")
            print("   4. Verify logs show: 'Coinstore API POST /spot/accountList response status=200'")
        else:
            print("❌ Failed to update bot status")
            sys.exit(1)
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
