#!/bin/bash
# Restore BitMart connector for client_sharp account
# Run this after trading-bridge restarts or updates

curl -X POST "https://trading-bridge-production.up.railway.app/connectors/add" \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "client_sharp",
    "connector_name": "bitmart",
    "api_key": "d8550cca6914e2b24c6374fa1ef00fe0fce62c32",
    "api_secret": "0916719bcca31383406e9d9bdbadff0d104d94bbe58f50eb9e33337341de204f",
    "memo": "test1"
  }'

echo ""
echo "Connector restored. Verify with:"
echo "curl 'https://trading-bridge-production.up.railway.app/portfolio?account=client_sharp'"
