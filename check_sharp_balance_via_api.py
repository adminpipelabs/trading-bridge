#!/usr/bin/env python3
"""
Check Sharp's BitMart balance via API endpoint.
This works without needing DATABASE_URL.
"""
import requests
import json
import sys

API_BASE = "https://trading-bridge-production.up.railway.app"

def check_balance_via_api():
    """Check balance using API endpoints."""
    
    print("🔍 Checking Sharp's BitMart balance via API...")
    print(f"   API Base: {API_BASE}\n")
    
    # Try to find Sharp's account identifier
    # Common patterns: client_sharp, sharp_foundation, etc.
    account_identifiers = [
        "client_sharp",
        "sharp_foundation", 
        "sharp",
        "client_new_sharp_foundation"
    ]
    
    print("📋 Trying account identifiers...")
    for account_id in account_identifiers:
        try:
            url = f"{API_BASE}/api/exchange/balance/{account_id}"
            print(f"\n   Trying: {account_id}")
            print(f"   URL: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                balances = data.get("balances", {})
                
                if balances:
                    print(f"\n✅ Found balances for {account_id}!")
                    print("\n" + "="*70)
                    print(f"💰 BITMART BALANCES FOR {account_id.upper()}")
                    print("="*70)
                    
                    bitmart_balances = balances.get("bitmart", {})
                    if bitmart_balances:
                        print(f"\n{'Currency':<12} {'Total':>20} {'Free':>20} {'Used':>20}")
                        print("-" * 70)
                        
                        for currency, balance_info in bitmart_balances.items():
                            if isinstance(balance_info, dict):
                                total = balance_info.get("total", 0)
                                free = balance_info.get("free", 0)
                                used = balance_info.get("used", 0)
                                if total > 0:
                                    print(f"{currency:<12} {total:>20,.8f} {free:>20,.8f} {used:>20,.8f}")
                        
                        # Check specifically for SHARP and USDT
                        sharp_bal = bitmart_balances.get("SHARP", {})
                        usdt_bal = bitmart_balances.get("USDT", {})
                        
                        if sharp_bal:
                            print(f"\n📊 SHARP Balance: {sharp_bal.get('total', 0):,.8f} SHARP")
                            print(f"   Free: {sharp_bal.get('free', 0):,.8f} SHARP")
                        else:
                            print("\n⚠️  SHARP balance: 0")
                        
                        if usdt_bal:
                            print(f"\n💵 USDT Balance: ${usdt_bal.get('total', 0):,.2f} USDT")
                            print(f"   Free: ${usdt_bal.get('free', 0):,.2f} USDT")
                        else:
                            print("\n⚠️  USDT balance: $0")
                        
                        print("="*70)
                        return True
                    else:
                        print(f"   ⚠️  No BitMart balances found")
                else:
                    print(f"   ⚠️  No balances returned")
            elif response.status_code == 404:
                print(f"   ❌ Account not found")
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ Could not find Sharp's account")
    print("\n💡 Try these options:")
    print("   1. Run SQL query in Railway PostgreSQL Query tab:")
    print("      See: check_sharp_balance.sql")
    print("   2. Use wallet address if known:")
    print(f"      curl '{API_BASE}/api/clients/balances?wallet_address=WALLET_ADDRESS'")
    print("   3. Check Railway logs for account identifier")
    
    return False


if __name__ == "__main__":
    try:
        check_balance_via_api()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(1)
