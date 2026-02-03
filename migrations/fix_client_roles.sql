-- CRITICAL SECURITY FIX: Ensure all clients have correct roles
-- Run this IMMEDIATELY to fix role assignments

-- Set ALL non-admin users to 'client' role
UPDATE clients SET role = 'client' WHERE account_identifier != 'admin' OR account_identifier IS NULL;

-- Ensure only the actual admin has admin role
UPDATE clients SET role = 'admin' WHERE account_identifier = 'admin';

-- Set default for any NULL roles (safety)
UPDATE clients SET role = 'client' WHERE role IS NULL;

-- Verify the fix
SELECT id, name, account_identifier, role FROM clients ORDER BY role, name;

-- Expected result:
-- All clients should have role = 'client'
-- Only admin account should have role = 'admin'
-- NO NULL roles
