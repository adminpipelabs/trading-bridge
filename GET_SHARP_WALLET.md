# Get Sharp's Wallet Address

## Quick SQL Query (Railway PostgreSQL)

Run this in Railway → PostgreSQL → Query tab:

```sql
SELECT 
    c.name as client_name,
    c.account_identifier,
    w.address as wallet_address
FROM clients c
LEFT JOIN wallets w ON w.client_id = c.id
WHERE c.name ILIKE '%sharp%' OR c.account_identifier ILIKE '%sharp%'
ORDER BY c.created_at DESC
LIMIT 5;
```

This will show Sharp's wallet address.

## Then Check Balance

Once you have the wallet address, run:

```bash
python3 check_balance_via_api.py WALLET_ADDRESS
```

Or use curl:

```bash
curl "https://trading-bridge-production.up.railway.app/api/clients/portfolio?wallet_address=WALLET_ADDRESS" | jq
```
