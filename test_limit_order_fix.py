#!/usr/bin/env python3
"""
Coinstore LIMIT Order Fix Test
Tests the corrected payload format:
  - ordPrice as NUMBER (not string)
  - ordQty as STRING
  - timestamp INCLUDED (required)

Run on Hetzner: python3 test_limit_order_fix.py
"""

import hashlib
import hmac
import json
import math
import time
import requests
import os
import sys
from sqlalchemy import create_engine, text
from cryptography.fernet import Fernet

BASE_URL = "https://api.coinstore.com/api"

def get_credentials():
    """Get credentials from database"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    
    if not DATABASE_URL or not ENCRYPTION_KEY:
        print("ERROR: DATABASE_URL or ENCRYPTION_KEY not set")
        sys.exit(1)
    
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT api_key_encrypted, api_secret_encrypted FROM exchange_credentials WHERE exchange = \'coinstore\' LIMIT 1'))
        row = result.fetchone()
        if not row:
            print("ERROR: No Coinstore credentials found")
            sys.exit(1)
        
        fernet = Fernet(ENCRYPTION_KEY.encode())
        api_key = fernet.decrypt(row[0].encode()).decode().strip()
        api_secret = fernet.decrypt(row[1].encode()).decode().strip()
        
        return api_key, api_secret.encode('utf-8')

def sign_request(secret, payload_str):
    expires = int(time.time() * 1000)
    expires_key = str(math.floor(expires / 30000)).encode("utf-8")
    key = hmac.new(secret, expires_key, hashlib.sha256).hexdigest()
    sig = hmac.new(key.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256).hexdigest()
    return sig, expires

def test_ticker():
    """Step 1: Get current SHARP price (no auth needed)"""
    print("\n" + "="*60)
    print("STEP 1: Fetch SHARPUSDT ticker")
    print("="*60)
    try:
        r = requests.get(f"{BASE_URL}/v1/market/tickers", timeout=10)
        data = r.json()
        for t in data.get("data", []):
            if t.get("symbol") == "SHARPUSDT":
                price = float(t["close"])
                print(f"  Last price: {price}")
                print(f"  Bid: {t.get('bid')}  Ask: {t.get('ask')}")
                return price
        print("  ERROR: SHARPUSDT not found in tickers")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def test_limit_order_OLD_format(price, api_key, secret):
    """Step 2a: Test OLD format (ordPrice as string, no timestamp) — should FAIL"""
    print("\n" + "="*60)
    print("STEP 2a: OLD format (ordPrice=string, no timestamp)")
    print("  Expected: 1401 error")
    print("="*60)
    
    bid_price = round(price * 0.80, 6)  # 20% below market, won't fill
    qty = round(10.0 / bid_price, 2)
    
    payload = json.dumps({
        "symbol": "SHARPUSDT",
        "side": "BUY",
        "ordType": "LIMIT",
        "ordPrice": str(bid_price),   # STRING — wrong per docs
        "ordQty": str(qty)
        # NO timestamp — wrong per docs
    })
    
    print(f"  Payload: {payload}")
    sig, expires = sign_request(secret, payload)
    headers = {
        "X-CS-APIKEY": api_key,
        "X-CS-SIGN": sig,
        "X-CS-EXPIRES": str(expires),
        "Content-Type": "application/json"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/trade/order/place", data=payload, headers=headers, timeout=10)
        print(f"  HTTP: {r.status_code}")
        print(f"  Response: {r.text}")
        resp = r.json()
        return resp.get("code", -1)
    except Exception as e:
        print(f"  ERROR: {e}")
        return -1

def test_limit_order_NEW_format(price, api_key, secret):
    """Step 2b: Test NEW format (ordPrice as number, timestamp included) — should SUCCEED"""
    print("\n" + "="*60)
    print("STEP 2b: NEW format (ordPrice=number, timestamp=included)")
    print("  Expected: code 0 (success)")
    print("="*60)
    
    bid_price = round(price * 0.80, 6)  # 20% below market, won't fill
    qty = round(10.0 / bid_price, 2)
    
    payload = json.dumps({
        "symbol": "SHARPUSDT",
        "side": "BUY",
        "ordType": "LIMIT",
        "ordPrice": bid_price,              # NUMBER — correct per docs
        "ordQty": str(qty),                 # STRING — correct per docs
        "timestamp": int(time.time() * 1000)  # INCLUDED — required per docs
    })
    
    print(f"  Payload: {payload}")
    sig, expires = sign_request(secret, payload)
    headers = {
        "X-CS-APIKEY": api_key,
        "X-CS-SIGN": sig,
        "X-CS-EXPIRES": str(expires),
        "Content-Type": "application/json"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/trade/order/place", data=payload, headers=headers, timeout=10)
        print(f"  HTTP: {r.status_code}")
        print(f"  Response: {r.text}")
        resp = r.json()
        return resp.get("code", -1), resp.get("data", {})
    except Exception as e:
        print(f"  ERROR: {e}")
        return -1, {}

def test_cancel_order(ord_id, api_key, secret):
    """Step 3: Cancel the test order if it was placed"""
    print("\n" + "="*60)
    print(f"STEP 3: Cancel order {ord_id}")
    print("="*60)
    
    payload = json.dumps({
        "symbol": "SHARPUSDT",
        "ordId": ord_id
    })
    
    sig, expires = sign_request(secret, payload)
    headers = {
        "X-CS-APIKEY": api_key,
        "X-CS-SIGN": sig,
        "X-CS-EXPIRES": str(expires),
        "Content-Type": "application/json"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/trade/order/cancel", data=payload, headers=headers, timeout=10)
        print(f"  HTTP: {r.status_code}")
        print(f"  Response: {r.text}")
    except Exception as e:
        print(f"  ERROR: {e}")

def main():
    print("="*60)
    print("COINSTORE LIMIT ORDER FIX TEST")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("="*60)
    
    # Get credentials
    api_key, secret = get_credentials()
    print(f"API Key: {api_key[:10]}...{api_key[-5:]}")
    
    # Step 1: Get price
    price = test_ticker()
    if not price:
        print("\nABORTED: Could not get SHARP price")
        return
    
    # Step 2a: Test OLD format (expect fail)
    old_code = test_limit_order_OLD_format(price, api_key, secret)
    
    # Step 2b: Test NEW format (expect success)
    new_code, data = test_limit_order_NEW_format(price, api_key, secret)
    
    # Step 3: Cancel if order was placed
    if new_code == 0 and data:
        ord_id = data.get("ordId") or data.get("order_id")
        if ord_id:
            test_cancel_order(ord_id, api_key, secret)
        else:
            print(f"\n  WARNING: Order placed but no ordId in response: {data}")
    
    # Summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"  OLD format (string price, no timestamp): code={old_code} {'FAILED as expected' if old_code != 0 else 'UNEXPECTEDLY WORKED'}")
    print(f"  NEW format (number price, with timestamp): code={new_code} {'SUCCESS — FIX CONFIRMED' if new_code == 0 else 'STILL FAILING — need more investigation'}")
    
    if new_code == 0:
        print("\n  >>> FIX: Change connector to send ordPrice as float, include timestamp <<<")
    elif old_code != 0 and new_code != 0:
        print("\n  >>> Both formats failed. Issue may be elsewhere. <<<")
        print("  >>> Check: min order size, price precision, account restrictions <<<")

if __name__ == "__main__":
    main()
