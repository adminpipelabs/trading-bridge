#!/usr/bin/env python3
"""
Sync BitMart connector from Hummingbot to trading-bridge database.
As CTO, this script retrieves credentials from Hummingbot and adds to trading-bridge.
"""
import os
import sys
import httpx
import yaml
import asyncio
from typing import Dict, Optional

# Trading Bridge endpoint
TRADING_BRIDGE_URL = "https://trading-bridge-production.up.railway.app"
CLIENT_ID = "70ab29b1-66ad-4645-aec8-fa2f55abe144"

# Hummingbot API (from environment)
HUMMINGBOT_API_URL = os.getenv("HUMMINGBOT_API_URL", "").strip()
HUMMINGBOT_USERNAME = os.getenv("HUMMINGBOT_API_USERNAME", "admin").strip()
HUMMINGBOT_PASSWORD = os.getenv("HUMMINGBOT_API_PASSWORD", "admin").strip()


async def get_credentials_from_hummingbot_api() -> Optional[Dict]:
    """Try to get BitMart credentials from Hummingbot API."""
    if not HUMMINGBOT_API_URL:
        print("❌ HUMMINGBOT_API_URL not set")
        return None
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try to get credentials endpoint (may not exist)
            url = f"{HUMMINGBOT_API_URL}/api/credentials/client_sharp/bitmart"
            response = await client.get(
                url,
                auth=(HUMMINGBOT_USERNAME, HUMMINGBOT_PASSWORD),
                headers={"ngrok-skip-browser-warning": "true"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  Hummingbot API returned {response.status_code}")
                return None
    except Exception as e:
        print(f"⚠️  Could not get credentials from Hummingbot API: {e}")
        return None


def get_credentials_from_file() -> Optional[Dict]:
    """Try to read credentials from local Hummingbot files."""
    possible_paths = [
        "bots/credentials/client_sharp/connectors/bitmart.yml",
        "/app/bots/credentials/client_sharp/connectors/bitmart.yml",
        os.path.expanduser("~/hummingbot/bots/credentials/client_sharp/connectors/bitmart.yml"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    return {
                        "api_key": data.get("bitmart_api_key") or data.get("api_key"),
                        "api_secret": data.get("bitmart_api_secret") or data.get("api_secret"),
                        "memo": data.get("bitmart_memo") or data.get("memo") or data.get("uid")
                    }
            except Exception as e:
                print(f"⚠️  Error reading {path}: {e}")
    
    return None


async def add_connector_to_trading_bridge(api_key: str, api_secret: str, memo: Optional[str] = None):
    """Add BitMart connector to trading-bridge database."""
    url = f"{TRADING_BRIDGE_URL}/clients/{CLIENT_ID}/connector"
    
    payload = {
        "name": "bitmart",
        "api_key": api_key,
        "api_secret": api_secret,
    }
    
    if memo:
        payload["memo"] = memo
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(url, json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"❌ Failed to add connector: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        raise


async def main():
    print("=" * 80)
    print("CTO: Syncing BitMart Connector from Hummingbot to Trading-Bridge")
    print("=" * 80)
    
    # Try to get credentials
    creds = None
    
    # Method 1: Try Hummingbot API
    print("\n1. Trying Hummingbot API...")
    creds = await get_credentials_from_hummingbot_api()
    
    # Method 2: Try local files
    if not creds:
        print("\n2. Trying local files...")
        creds = get_credentials_from_file()
    
    # Method 3: Use environment variables (if set)
    if not creds:
        print("\n3. Checking environment variables...")
        api_key = os.getenv("BITMART_API_KEY")
        api_secret = os.getenv("BITMART_API_SECRET")
        memo = os.getenv("BITMART_MEMO")
        
        if api_key and api_secret:
            creds = {
                "api_key": api_key,
                "api_secret": api_secret,
                "memo": memo
            }
    
    if not creds or not creds.get("api_key") or not creds.get("api_secret"):
        print("\n❌ Could not retrieve BitMart credentials automatically.")
        print("\nPlease provide credentials manually:")
        print("\nOption 1: Set environment variables:")
        print("  export BITMART_API_KEY='your_key'")
        print("  export BITMART_API_SECRET='your_secret'")
        print("  export BITMART_MEMO='your_memo'")
        print("  python3 sync_connector_from_hummingbot.py")
        print("\nOption 2: Run curl command directly:")
        print(f"  curl -X PUT '{TRADING_BRIDGE_URL}/clients/{CLIENT_ID}/connector' \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"name\": \"bitmart\", \"api_key\": \"...\", \"api_secret\": \"...\", \"memo\": \"...\"}'")
        sys.exit(1)
    
    print(f"\n✅ Found credentials:")
    print(f"   API Key: {creds['api_key'][:10]}...")
    print(f"   API Secret: {'*' * 20}")
    print(f"   Memo: {creds.get('memo', 'N/A')}")
    
    # Add to trading-bridge
    print(f"\n4. Adding connector to trading-bridge...")
    try:
        result = await add_connector_to_trading_bridge(
            creds["api_key"],
            creds["api_secret"],
            creds.get("memo")
        )
        print("✅ Connector added successfully!")
        print(f"\nResult: {result}")
        
        # Verify
        print("\n5. Verifying connector...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            verify_response = await client.get(
                f"{TRADING_BRIDGE_URL}/clients/{CLIENT_ID}"
            )
            verify_data = verify_response.json()
            connectors = verify_data.get("connectors", [])
            if connectors:
                print(f"✅ Verified: {len(connectors)} connector(s) found")
                for conn in connectors:
                    print(f"   - {conn.get('name')}: {conn.get('id')}")
            else:
                print("⚠️  Warning: No connectors found after adding")
        
        print("\n" + "=" * 80)
        print("✅ SUCCESS: BitMart connector synced to trading-bridge")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Failed to add connector: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("⚠️  pyyaml not installed. Install with: pip install pyyaml")
        print("   Or use curl command directly.")
        sys.exit(1)
    
    asyncio.run(main())
