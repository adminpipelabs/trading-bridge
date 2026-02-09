# Action Plan: Fix Coinstore 1401 Unauthorized Error

## Current Status
✅ Code is correct (signature, payload, headers all match Coinstore docs)
❌ API returns `1401 Unauthorized` on Railway
✅ Detailed logging shows exact request being sent

## Priority Actions (Do These First)

### 1. ✅ Verify Local Test Uses Database Keys

**Run this locally** (with DATABASE_URL set):
```bash
# Set your database URL
export DATABASE_URL="your_database_url_here"

# Test with database keys
python3 test_coinstore_keys_direct.py
```

**What to check:**
- If it works locally → Issue is Railway-specific (IP/permissions)
- If it fails locally → Issue is with the keys themselves (wrong/corrupted)

### 2. 🔍 Check Coinstore API Key Settings

**Log into Coinstore Dashboard:**
1. Go to API Key management
2. Find key: `42b5c7c40bf625e7fcffd16a654b6ed0`
3. Verify:
   - ✅ **"Spot Trading" permission is ENABLED**
   - ✅ **IP whitelist includes `54.205.35.75`** (Railway's current IP)
   - ✅ **Key is ACTIVE** (not revoked/expired)

**If IP whitelist is enabled:**
- Add `54.205.35.75` to whitelist
- Railway may also use `3.222.129.4` - add both if possible
- OR disable IP whitelist entirely (if allowed)

### 3. 🔄 Test Signature Generation Locally

**Create a simple test script** to verify signature matches:

```python
#!/usr/bin/env python3
import json
import hmac
import hashlib
import math
import time

# Use EXACT same keys from database
api_key = "42b5c7c40bf625e7fcffd16a654b6ed0"
api_secret = "<your_secret_from_database>"  # Get from database

# Use EXACT same timestamp as Railway
expires = 1770677890477  # From Railway logs
expires_key = str(math.floor(expires / 30000))
payload = json.dumps({})

# Generate signature (same as Railway)
key = hmac.new(api_secret.encode("utf-8"), expires_key.encode("utf-8"), hashlib.sha256).hexdigest()
signature = hmac.new(key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

print(f"Expires: {expires}")
print(f"Expires Key: {expires_key}")
print(f"Payload: '{payload}'")
print(f"Signature: {signature}")
print(f"\nExpected (from Railway): b681b1dfb4fe23effc5815ebfbdc214ded6db952254d63762c1fb70c7060bb5f")
print(f"Match: {signature == 'b681b1dfb4fe23effc5815ebfbdc214ded6db952254d63762c1fb70c7060bb5f'}")
```

**If signatures match** → Code is correct, issue is permissions/IP
**If signatures differ** → There's a key mismatch or encoding issue

## Quick Fixes to Try

### Option A: Disable IP Whitelist (If Possible)
1. Go to Coinstore API key settings
2. Disable IP whitelist restriction
3. Test again

### Option B: Add Both Railway IPs
1. Add `54.205.35.75` to whitelist
2. Add `3.222.129.4` to whitelist (Railway alternates)
3. Test again

### Option C: Verify API Key Permissions
1. Ensure "Spot Trading" permission is enabled
2. Ensure "Read" permission is enabled
3. Re-test

## If Nothing Works

### Contact Coinstore Support
Provide them with:
- API Key: `42b5c7c40bf625e7fcffd16a654b6ed0`
- Error: `1401 Unauthorized`
- Request details from logs:
  - Endpoint: `POST /api/spot/accountList`
  - Headers: (from Railway logs)
  - Signature: `b681b1dfb4fe23effc5815ebfbdc214ded6db952254d63762c1fb70c7060bb5f`
  - Expires: `1770677890477`

Ask them to verify:
- Is the API key active?
- Does it have spot trading permissions?
- Is there an IP restriction blocking Railway?
- Is the signature format correct?

## Expected Outcome

After checking permissions/IP:
- ✅ If fixed → Balances will show on dashboard
- ❌ If still failing → Need Coinstore support to investigate

## Next Steps After Fix

1. ✅ Verify balances show on dashboard
2. ✅ Test with a small trade (if needed)
3. ✅ Remove excessive debug logging (optional)
4. ✅ Document the fix for future reference
