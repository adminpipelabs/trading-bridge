# Register Admin Solana Wallet

## Admin Wallet Address
```
BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV
```

## Option 1: Run SQL Script (Recommended)

1. **Go to Railway Dashboard**
2. **Find PostgreSQL service** → Click on it
3. **Go to "Data" tab** → Click "Query"
4. **Copy and paste** the SQL from `register_admin_wallet.sql`
5. **Run the query**

## Option 2: Use Railway CLI

```bash
railway connect postgres
psql < register_admin_wallet.sql
```

## Option 3: Use Admin UI (After Login)

Once you can log in with another admin account:
1. Go to Admin Dashboard
2. Create new client with:
   - Name: "Admin"
   - Wallet: `BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV`
   - Chain: Solana
   - Account Identifier: `admin`
   - Role: `admin`

## What It Does

- Creates/updates admin client with `account_identifier = "admin"`
- Sets `role = "admin"`
- Links Solana wallet `BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV`
- Stores wallet in original case (case-sensitive)

## Verify

After running, you should be able to:
1. Log in with Solana wallet `BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV`
2. Get admin role automatically
3. Access admin features
