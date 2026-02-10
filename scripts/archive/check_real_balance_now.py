#!/usr/bin/env python3
"""
Check REAL balance from BitMart API using Sharp's API keys.
This queries BitMart directly to get actual account balance.
"""
import requests
import json
import sys

API_BASE = "https://trading-bridge-production.up.railway.app"

def check_real_balance():
    """Check real balance via API endpoints."""
    
    print("="*70)
    print("🔍 CHECKING REAL BALANCE FROM BITMART API")
    print("="*70)
    print(f"\nAPI Base: {API_BASE}\n")
    
    account_id = "client_new_sharp_foundation"
    
    # Try multiple endpoints
    endpoints = [
        ("Exchange Balance", f"/api/exchange/balance/{account_id}"),
        ("Exchange Dashboard", f"/api/exchange/dashboard/{account_id}"),
    ]
    
    results = {}
    
    for name, endpoint in endpoints:
        try:
            url = f"{API_BASE}{endpoint}"
            print(f"📡 Checking: {name}")
            print(f"   URL: {url}")
            
            response = requests.get(url, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results[name] = data
                
                # Extract balance info
                if "balances" in data:
                    balances = data["balances"]
                    if isinstance(balances, dict) and balances:
                        print(f"   ✅ Found balances!")
                        for exchange, exchange_balances in balances.items():
                            if isinstance(exchange_balances, dict):
                                for asset, balance_info in exchange_balances.items():
                                    if isinstance(balance_info, dict):
                                        total = balance_info.get("total", 0)
                                        if total > 0:
                                            print(f"      💰 {exchange} {asset}: {total}")
                    elif isinstance(balances, list) and balances:
                        print(f"   ✅ Found {len(balances)} balance(s)!")
                        for bal in balances:
                            asset = bal.get("asset", "unknown")
                            total = bal.get("total", 0)
                            if total > 0:
                                print(f"      💰 {asset}: {total}")
                    else:
                        print(f"   ⚠️  No balances found")
                elif "balance" in data:
                    balance_data = data["balance"]
                    if isinstance(balance_data, dict):
                        balances_list = balance_data.get("balances", [])
                        total_usdt = balance_data.get("total_usdt", 0)
                        if balances_list:
                            print(f"   ✅ Found {len(balances_list)} balance(s)!")
                            print(f"   💵 Total USD: ${total_usdt:,.2f}")
                            for bal in balances_list:
                                asset = bal.get("asset", "unknown")
                                total = bal.get("total", 0)
                                if total > 0:
                                    print(f"      💰 {asset}: {total:,.8f}")
                        else:
                            print(f"   ⚠️  No balances found")
                else:
                    print(f"   ⚠️  Response format unexpected")
                    print(f"   Response keys: {list(data.keys())}")
            else:
                print(f"   ❌ Error {response.status_code}")
                print(f"   Response: {response.text[:200]}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
    
    # Summary
    print("="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    # Try to get wallet address for client endpoint
    print("\n💡 To check via client endpoint, need wallet address.")
    print("   Run this SQL in Railway PostgreSQL:")
    print("   SELECT w.address FROM wallets w JOIN clients c ON c.id = w.client_id")
    print("   WHERE c.account_identifier = 'client_new_sharp_foundation';")
    print("\n   Then run:")
    print(f"   curl '{API_BASE}/api/clients/portfolio?wallet_address=WALLET_ADDRESS' | jq")
    
    # Show what we found
    if results:
        print("\n✅ Results from API calls:")
        for name, data in results.items():
            print(f"\n{name}:")
            print(json.dumps(data, indent=2)[:500])
    else:
        print("\n❌ No successful API calls")
        print("\n🔍 Likely causes:")
        print("   1. Connectors not in database")
        print("   2. Connectors not syncing")
        print("   3. API keys invalid")
        print("\n📋 Next steps:")
        print("   1. Check Railway logs for sync errors")
        print("   2. Verify connectors exist in database")
        print("   3. Add connectors if missing")


if __name__ == "__main__":
    check_real_balance()
