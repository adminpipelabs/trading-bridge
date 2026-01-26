# Password Mismatch Issue

**Date:** 2026-01-26  
**Issue:** Railway shows "admin" but debug endpoint shows different password

---

## 🔍 **Debug Results**

**Railway UI shows:** `HUMMINGBOT_API_PASSWORD = "admin"`

**Debug endpoint shows:**
- `password_length: 8`
- `password_first_char: "p"`
- `auth_header_preview: "Basic YWRtaW46cGFzc3dvcmQ=..."`

**Decoded auth header:** `admin:password`

---

## 🐛 **Problem**

Railway is reading `"password"` (8 chars) instead of `"admin"` (5 chars).

---

## 🔧 **Possible Causes**

1. **Railway has cached/stale value**
   - UI shows "admin" but actual stored value is "password"
   - Need to delete and recreate the variable

2. **Whitespace in password**
   - Password might be `"admin "` (with trailing space) = 8 chars
   - Or `" password"` (with leading space)

3. **Different environment variable**
   - Maybe ` HUMMINGBOT_API_PASSWORD` (with space) has different value
   - Check all variations

4. **Railway UI masking issue**
   - UI shows "admin" but stored value is different

---

## ✅ **Fix Steps**

1. **Delete the variable in Railway**
   - Remove `HUMMINGBOT_API_PASSWORD`

2. **Recreate it with exact value**
   - Set `HUMMINGBOT_API_PASSWORD = admin` (no spaces, exactly 5 characters)

3. **Verify after redeploy**
   - Check `/debug/env` endpoint
   - Should show `password_length: 5` and `password_first_char: "a"`

4. **Test bot creation again**

---

**Action Required:** Update Railway `HUMMINGBOT_API_PASSWORD` to exactly `admin` (5 chars, no spaces)
