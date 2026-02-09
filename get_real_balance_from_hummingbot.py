#!/usr/bin/env python3
"""
Get REAL balance from BitMart using API keys from Hummingbot credential files.
This queries BitMart directly to show actual account balance.
"""
import os
import sys
import yaml
import asyncio
import ccxt.async_support as ccxt
from pathlib import Path

def find_hummingbot_credentials(account_identifier: str = "client_new_sharp_foundation"):
    """Find BitMart credentials from Hummingbot files."""
    
    possible_paths = [
        f"bots/credentials/{account_identifier}/connectors/bitmart.yml",
        f"/app/bots/credentials/{account_identifier}/connectors/bitmart.yml",
        os.path.expanduser(f"~/hummingbot/bots/credentials/{account_identifier}/connectors/bitmart.yml"),
        os.path.expanduser(f"~/hummingbot_files/bots/credentials/{account_identifier}/connectors/bitmart.yml"),
        # Also try client_sharp (old name)
        "bots/credentials/client_sharp/connectors/bitmart.yml",
        os.path.expanduser("~/hummingbot/bots/credentials/client_sharp/connectors/bitmart.yml"),
    ]
    
    print("🔍 Looking for Hummingbot credential files...")
    for path in possible_paths:
        full_path = Path(path)
        if full_path.exists():
            print(f"✅ Found: {full_path}")
            try:
                with open(full_path, 'r') as f:
                    data = yaml.safe_load(f)
                    api_key = data.get("bitmart_api_key") or data.get("api_key")
                    api_secret = data.get("bitmart_api_secret") or data.get("api_secret")
                    memo = data.get("bitmart_memo") or data.get("memo") or data.get("uid")
                    
                    if api_key and api_secret:
                        return {
                            "api_key": api_key,
                            "api_secret": api_secret,
                            "memo": memo
                        }
            except Exception as e:
                print(f"⚠️  Error reading {path}: {e}")
    
    print("❌ No Hummingbot credential files found")
    return None


async def get_real_balance_from_bitmart(api_key: str, api_secret: str, memo: str = None):
    """Query BitMart API directly to get REAL balance."""
    
    print("\n🔍 Connecting to BitMart API...")
    print(f"   API Key: {api_key[:15]}...")
    if memo:
        print(f"   Memo/UID: {memo}")
    
    exchange_params = {
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    }
    
    if memo:
        exchange_params['uid'] = memo
    
    exchange = ccxt.bitmart(exchange_params)
    
    try:
        print("   Loading markets...")
        await exchange.load_markets()
        print("✅ Markets loaded")
        
        print("\n💰 Fetching REAL balance from BitMart...")
        balance = await exchange.fetch_balance()
        
        # Display balances
        print("\n" + "="*70)
        print("💰 REAL BITMART BALANCE (from API)")
        print("="*70)
        
        non_zero = []
        for currency, amounts in balance.get("total", {}).items():
            total = float(amounts) if amounts else 0
            if total > 0:
                free = float(balance.get("free", {}).get(currency, 0))
                used = float(balance.get("used", {}).get(currency, 0))
                non_zero.append({
                    "currency": currency,
                    "total": total,
                    "free": free,
                    "used": used
                })
        
        if non_zero:
            print(f"\n{'Currency':<12} {'Total':>20} {'Free':>20} {'Used':>20}")
            print("-" * 70)
            for bal in sorted(non_zero, key=lambda x: x['total'], reverse=True):
                print(f"{bal['currency']:<12} {bal['total']:>20,.8f} {bal['free']:>20,.8f} {bal['used']:>20,.8f}")
            print("="*70)
            
            # Calculate total USD (USDT = 1:1)
            usdt_bal = next((b for b in non_zero if b['currency'] == 'USDT'), None)
            total_usd = usdt_bal['total'] if usdt_bal else 0
            
            print(f"\n💵 Total USD Value: ${total_usd:,.2f}")
            
            # Check specifically for SHARP and USDT
            sharp_bal = next((b for b in non_zero if b['currency'] == 'SHARP'), None)
            if sharp_bal:
                print(f"\n📊 SHARP Balance: {sharp_bal['total']:,.8f} SHARP")
                print(f"   Free: {sharp_bal['free']:,.8f} SHARP")
            else:
                print("\n⚠️  SHARP balance: 0")
            
            if usdt_bal:
                print(f"\n💵 USDT Balance: ${usdt_bal['total']:,.2f} USDT")
                print(f"   Free: ${usdt_bal['free']:,.2f} USDT")
            else:
                print("\n⚠️  USDT balance: $0")
            
            print("\n✅ This is the REAL balance from BitMart API")
            print("   Client will see this in dashboard once connectors are synced")
            
        else:
            print("\n⚠️  All balances are zero")
            print("="*70)
            print("\n✅ This is the REAL balance (account is empty)")
        
        await exchange.close()
        return non_zero
        
    except Exception as e:
        print(f"\n❌ Failed to fetch balance: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    print("="*70)
    print("🔍 GET REAL BALANCE FROM BITMART USING HUMMINGBOT CREDENTIALS")
    print("="*70)
    
    # Try to get credentials from Hummingbot files
    creds = find_hummingbot_credentials()
    
    if not creds:
        print("\n❌ Could not find Hummingbot credential files")
        print("\n💡 Options:")
        print("   1. Check if Hummingbot files exist locally")
        print("   2. Use API keys directly (set environment variables):")
        print("      export BITMART_API_KEY='...'")
        print("      export BITMART_API_SECRET='...'")
        print("      export BITMART_MEMO='...'")
        print("      python3 get_real_balance_from_hummingbot.py")
        
        # Try environment variables as fallback
        api_key = os.getenv("BITMART_API_KEY")
        api_secret = os.getenv("BITMART_API_SECRET")
        memo = os.getenv("BITMART_MEMO")
        
        if api_key and api_secret:
            print("\n✅ Found credentials in environment variables")
            creds = {
                "api_key": api_key,
                "api_secret": api_secret,
                "memo": memo
            }
        else:
            sys.exit(1)
    
    # Get real balance
    balances = await get_real_balance_from_bitmart(
        creds["api_key"],
        creds["api_secret"],
        creds.get("memo")
    )
    
    if balances:
        print("\n" + "="*70)
        print("✅ SUCCESS: Got REAL balance from BitMart")
        print("="*70)
        print("\n📋 Next steps:")
        print("   1. Add these API keys to trading-bridge database (connectors table)")
        print("   2. Client dashboard will then show this balance")
        print("   3. Volume bot will be able to trade with these funds")


if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("❌ pyyaml not installed")
        print("   Install: pip install pyyaml")
        sys.exit(1)
    
    asyncio.run(main())
