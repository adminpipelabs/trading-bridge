#!/usr/bin/env python3
"""
Check Sharp's BitMart balance via API endpoint.
This works without needing direct database access.
"""
import requests
import json
import sys

API_BASE = "https://trading-bridge-production.up.railway.app"

def check_balance_via_api(wallet_address=None):
    """Check balance using API endpoint."""
    
    if not wallet_address:
        print("❌ Need wallet address")
        print("\nTo get wallet address:")
        print("1. Check Railway PostgreSQL Query tab:")
        print("   SELECT w.address FROM wallets w JOIN clients c ON c.id = w.client_id WHERE c.name ILIKE '%sharp%';")
        print("\n2. Or use debug endpoint to find it:")
        print(f"   curl '{API_BASE}/api/clients/debug?wallet_address=WALLET'")
        return
    
    print(f"🔍 Checking balance for wallet: {wallet_address}")
    print(f"   API: {API_BASE}\n")
    
    try:
        # Use portfolio endpoint (includes balances + bot counts)
        url = f"{API_BASE}/api/clients/portfolio?wallet_address={wallet_address}"
        print(f"📡 Calling: {url}")
        
        response = requests.get(url, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "error" in data:
                print(f"\n❌ Error: {data['error']}")
                print(f"   Message: {data.get('message', 'No message')}")
                return
            
            balances = data.get("balances", [])
            total_usd = data.get("total_usd", 0)
            account = data.get("account", "unknown")
            
            print(f"\n✅ Account: {account}")
            print(f"✅ Total USD: ${total_usd:,.2f}")
            
            if balances:
                print(f"\n💰 BALANCES ({len(balances)} token(s)):")
                print("="*70)
                print(f"{'Exchange':<12} {'Asset':<12} {'Total':>20} {'Free':>20} {'USD Value':>15}")
                print("-" * 70)
                
                for bal in balances:
                    exchange = bal.get("exchange", "unknown")
                    asset = bal.get("asset", "unknown")
                    total = bal.get("total", 0)
                    free = bal.get("free", 0)
                    usd_value = bal.get("usd_value", 0)
                    
                    print(f"{exchange:<12} {asset:<12} {total:>20,.8f} {free:>20,.8f} ${usd_value:>14,.2f}")
                
                print("="*70)
                
                # Check specifically for SHARP and USDT
                sharp_bal = next((b for b in balances if b.get("asset") == "SHARP"), None)
                usdt_bal = next((b for b in balances if b.get("asset") == "USDT"), None)
                
                if sharp_bal:
                    print(f"\n📊 SHARP: {sharp_bal['total']:,.8f} SHARP (Free: {sharp_bal['free']:,.8f})")
                else:
                    print("\n⚠️  SHARP: 0")
                
                if usdt_bal:
                    print(f"💵 USDT: ${usdt_bal['total']:,.2f} USDT (Free: ${usdt_bal['free']:,.2f})")
                else:
                    print("⚠️  USDT: $0")
                
                print(f"\n✅ Bot Status: {data.get('active_bots', 0)}/{data.get('total_bots', 0)} active")
            else:
                print("\n⚠️  No balances found")
                print("   This could mean:")
                print("   - API keys not configured")
                print("   - Connectors not syncing")
                print("   - Balance fetch failing")
                print("\n   Check Railway logs for details")
        else:
            print(f"\n❌ API Error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    wallet = sys.argv[1] if len(sys.argv) > 1 else None
    check_balance_via_api(wallet)
