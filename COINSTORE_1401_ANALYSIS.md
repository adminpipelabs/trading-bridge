# Coinstore 1401 Unauthorized Error - Detailed Analysis

## Date: 2026-02-09 22:58 UTC

## Request Details (from Railway logs)

### Balance Request (POST /spot/accountList)
- **API Key**: `42b5c7c40bf625e7fcffd16a654b6ed0`
- **Secret Length**: 32 characters ✅
- **URL**: `https://api.coinstore.com/api/spot/accountList` ✅
- **Method**: POST ✅
- **Payload**: `'{}'` ✅
- **Expires**: `1770677890477`
- **Expires Key**: `59022587`
- **Signature**: `b681b1dfb4fe23effc5815ebfbdc214ded6db952254d63762c1fb70c7060bb5f`
- **Response**: `{"message":"Unauthorized","code":1401}` ❌

### Headers Sent
```
Content-Type: application/json ✅
Accept: */* ✅
Connection: keep-alive ✅
X-CS-APIKEY: 42b5c7c40bf625e7fcffd16a654b6ed0 ✅
X-CS-SIGN: b681b1dfb4fe23effc5815ebfbdc214ded6db952254d63762c1fb70c7060bb5f ✅
X-CS-EXPIRES: 1770677890477 ✅
exch-language: en_US ✅
```

## Code Verification

### ✅ Signature Generation
- Algorithm matches Coinstore docs exactly
- Two-step HMAC-SHA256: `HMAC(secret, expires_key)` then `HMAC(derived_key, payload)`
- Payload for empty POST: `'{}'` (correct)
- Expires key calculation: `floor(expires / 30000)` (correct)

### ✅ Request Format
- URL construction: Correct (`BASE_URL + endpoint`)
- Payload encoding: Correct (`json.dumps({})` for empty POST)
- Headers: All required headers present
- Body: Sent as JSON (`json=` parameter in aiohttp)

### ✅ Key Handling
- Whitespace stripping: Applied in both `client_data.py` and `CoinstoreConnector.__init__`
- Decryption: Using `decrypt_credential` from `app.security`
- Key lengths: API key (32) and secret (32) match expected lengths

## Possible Causes

### 1. IP Whitelist Issue ⚠️
**Status**: Unlikely but possible
- Railway outbound IP: `54.205.35.75` (from logs)
- Coinstore configured for: `3.222.129.4` (from user)
- **Note**: User reported both IPs were tried and neither worked

### 2. API Key Permissions ❓
**Status**: Unknown - needs verification
- API key may not have "spot trading" permissions enabled
- Check Coinstore API key settings in their dashboard

### 3. Database vs Local Keys Mismatch ❓
**Status**: Unknown - needs verification
- User said keys work locally
- **Question**: Are the local test keys the same as database keys?
- **Action**: Verify local test script uses keys from database

### 4. API Key/Secret Corruption ❓
**Status**: Unlikely but possible
- Encryption/decryption might be corrupting keys
- **Action**: Compare decrypted keys with original input

## Next Steps

### Immediate Actions

1. **Verify Local Test Uses Database Keys**
   ```bash
   # Run test script that reads from database
   python3 test_coinstore_keys_direct.py
   ```
   - If this works locally but fails on Railway → IP/permissions issue
   - If this fails locally → Key corruption or wrong keys

2. **Check Coinstore API Key Settings**
   - Log into Coinstore dashboard
   - Verify API key `42b5c7c40bf625e7fcffd16a654b6ed0`:
     - Has "Spot Trading" permission enabled
     - IP whitelist includes `54.205.35.75` OR is disabled
     - Key is active (not revoked/expired)

3. **Compare Signature Generation**
   - Run local test with exact same `expires` timestamp
   - Compare generated signature byte-for-byte
   - If signatures match → Issue is not in code, likely permissions/IP
   - If signatures differ → Issue in signature generation

### Diagnostic Commands

```bash
# Test with database keys locally
python3 test_coinstore_keys_direct.py

# Test signature generation only
python3 test_coinstore_signature_unit.py

# Manual test with environment variables
export COINSTORE_API_KEY=42b5c7c40bf625e7fcffd16a654b6ed0
export COINSTORE_API_SECRET=<secret_from_database>
python3 test_coinstore_signature_manual.py
```

## Conclusion

**Code appears correct** ✅
- Signature generation matches Coinstore docs
- Request format is correct
- Headers are correct
- Payload is correct

**Most likely causes**:
1. API key permissions (spot trading not enabled)
2. IP whitelist mismatch (though user said both IPs tried)
3. Database keys differ from working local keys

**Recommendation**: 
1. Verify local test uses exact same keys from database
2. Check Coinstore API key permissions in dashboard
3. If both pass, contact Coinstore support with exact request details
