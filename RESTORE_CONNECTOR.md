# Restore Connector After Trading Bridge Updates

After trading-bridge restarts or updates, connectors are lost (stored in memory). Use this command to restore:

## Quick Restore Command

```bash
curl -X POST "https://trading-bridge-production.up.railway.app/connectors/add" \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "client_sharp",
    "connector_name": "bitmart",
    "api_key": "d8550cca6914e2b24c6374fa1ef00fe0fce62c32",
    "api_secret": "0916719bcca31383406e9d9bdbadff0d104d94bbe58f50eb9e33337341de204f",
    "memo": "test1"
  }'
```

## Or use the script

```bash
./restore_connector.sh
```

## Verify it worked

```bash
curl "https://trading-bridge-production.up.railway.app/portfolio?account=client_sharp"
```

You should see balance data with SHARP and USDT balances.

## Alternative: Use Pipe Labs Dashboard Sync

Instead of manually restoring, you can use the admin sync endpoint:

```bash
POST https://pipelabs-dashboard-production.up.railway.app/api/admin/sync-api-keys-to-trading-bridge
```

This will sync all active API keys from the database to trading-bridge.
