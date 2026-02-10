#!/usr/bin/env python3
"""Test authentication directly"""
import httpx
import base64
import asyncio
import os

async def test_auth():
    # Get credentials
    username = os.getenv("HUMMINGBOT_API_USERNAME", "admin")
    password = os.getenv("HUMMINGBOT_API_PASSWORD", "admin")
    base_url = os.getenv("HUMMINGBOT_API_URL", "https://unpolymerized-singlemindedly-theda.ngrok-free.dev")
    
    print(f"Username: '{username}' (length: {len(username)})")
    print(f"Password: '{password}' (length: {len(password)})")
    print(f"Base URL: {base_url}")
    
    # Manually construct Authorization header
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "ngrok-skip-browser-warning": "true",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    print(f"\nHeaders: {list(headers.keys())}")
    print(f"Authorization header: Basic {encoded_credentials[:20]}...")
    
    # Test request
    url = f"{base_url}/bot-orchestration/status"
    print(f"\nTesting: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())
