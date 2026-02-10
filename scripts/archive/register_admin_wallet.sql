-- Register Admin Solana Wallet
-- Run this SQL script on your Railway PostgreSQL database

-- Admin wallet address
-- BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV

-- Step 1: Create or update admin client
INSERT INTO clients (id, name, account_identifier, role, wallet_address, wallet_type, created_at, updated_at)
VALUES (
    gen_random_uuid()::text,
    'Admin',
    'admin',
    'admin',
    'BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV',
    'SOLANA',
    NOW(),
    NOW()
)
ON CONFLICT (account_identifier) 
DO UPDATE SET 
    role = 'admin',
    wallet_address = 'BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV',
    wallet_type = 'SOLANA',
    updated_at = NOW();

-- Step 2: Get admin client ID
-- (We'll use a subquery in the next step)

-- Step 3: Create or update admin wallet
INSERT INTO wallets (id, client_id, chain, address, created_at)
SELECT 
    gen_random_uuid()::text,
    c.id,
    'solana',
    'BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV',
    NOW()
FROM clients c
WHERE c.account_identifier = 'admin'
ON CONFLICT DO NOTHING;

-- Verify
SELECT 
    c.id,
    c.name,
    c.account_identifier,
    c.role,
    w.address as wallet_address,
    w.chain
FROM clients c
LEFT JOIN wallets w ON w.client_id = c.id
WHERE c.account_identifier = 'admin';
