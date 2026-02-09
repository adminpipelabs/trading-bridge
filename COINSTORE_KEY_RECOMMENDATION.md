# Coinstore API Key Recommendation

## ✅ Keep Current Key - Add Both IPs

### Recommendation: **Keep the current API key** and add **BOTH** Railway IPs to whitelist

**Current Setup:**
- API Key: `42b5c7c40bf625e7fcffd16a654b6ed0`
- IP Whitelist: `3.222.129.4` only
- Permissions: Read, Trade ✅
- Status: Valid ✅

**Problem:**
- Railway alternates between two IPs
- Only one IP is whitelisted
- When Railway uses the non-whitelisted IP → 1401 error

## 🛠️ Fix: Add Both IPs

### Step 1: Update IP Whitelist

1. Go to Coinstore API Key Management
2. Edit API Key: `42b5c7c40bf625e7fcffd16a654b6ed0`
3. Update IP whitelist to include **BOTH**:
   ```
   3.222.129.4
   54.205.35.75
   ```
4. Save changes
5. Wait 1-2 minutes
6. Test again

### Why Both IPs?

Railway uses QuotaGuard proxy which **alternates** between:
- `3.222.129.4` (currently whitelisted)
- `54.205.35.75` (NOT whitelisted - causes 1401)

**Both must be whitelisted** for consistent access.

## ❌ Don't Replace Key (Yet)

**Reasons to keep current key:**
- ✅ Permissions are correct
- ✅ Key is valid
- ✅ Code is correct
- ✅ Only issue is IP whitelist

**Only replace key if:**
- Adding both IPs doesn't work
- Coinstore support confirms key issue
- You want to test with a fresh key

## 🔄 Alternative: Two Keys (If Coinstore Allows)

If Coinstore allows multiple API keys:
- **Key 1**: `3.222.129.4` only
- **Key 2**: `54.205.35.75` only

**But this is more complex** - better to whitelist both IPs on one key.

## ✅ Expected Result

After adding `54.205.35.75` to whitelist:
- ✅ Both Railway IPs whitelisted
- ✅ No more 1401 errors
- ✅ Balances will show
- ✅ Consistent access regardless of which IP Railway uses

## 📝 Summary

**Action:** Keep current key, add both IPs to whitelist  
**Don't:** Replace key unless absolutely necessary  
**Test:** After adding both IPs, refresh dashboard
