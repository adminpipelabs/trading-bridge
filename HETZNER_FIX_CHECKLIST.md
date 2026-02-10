# Hetzner Fix Checklist

**Goal:** Get Coinstore working on Hetzner (IP: 5.161.64.209)

---

## ✅ **Step 1: Run Diagnostic**

```bash
cd /opt/trading-bridge
source venv/bin/activate
python3 test_coinstore_direct.py
```

**This will show:**
- Exact API key being used
- API secret preview
- Full API response
- Clear error message if 1401

---

## ✅ **Step 2: Check Coinstore Dashboard**

1. **Log into Coinstore**
2. **Go to API Management**
3. **Find API Key:** `42b5c7c40bf625e7fcffd16a654b6ed0`

**Verify:**
- ✅ IP `5.161.64.209` is in IP binding list
- ✅ API secret matches what script shows (no extra spaces)
- ✅ Permissions: "Read" ✅ and "Spot Trading" ✅ enabled

---

## ✅ **Step 3: Check Environment Variables**

```bash
# On Hetzner, check if proxy is set (should be empty on Hetzner)
echo $QUOTAGUARDSTATIC_URL
echo $QUOTAGUARD_PROXY_URL
```

**On Hetzner, these should be EMPTY** (we don't need proxy, we have static IP)

---

## ✅ **Step 4: Check Bot Logs**

```bash
journalctl -u trading-bridge -f | grep -i coinstore
```

**Look for:**
- `❌ COINSTORE 1401 UNAUTHORIZED` (with detailed diagnostics)
- `Using proxy: False` (should be False on Hetzner)
- Balance fetch errors

---

## 🔧 **Common Issues**

### Issue 1: IP Not Whitelisted
**Fix:** Add `5.161.64.209` to IP binding list on Coinstore dashboard

### Issue 2: Wrong API Secret
**Fix:** Compare secret in database vs Coinstore dashboard - must match EXACTLY

### Issue 3: Proxy Still Being Used
**Fix:** Unset `QUOTAGUARDSTATIC_URL` on Hetzner (we don't need it)

---

## 🚀 **After Fix**

**Success indicators:**
- ✅ `test_coinstore_direct.py` returns balance data (code 0)
- ✅ Bot logs show: `💰 Balance: X SHARP, Y USDT`
- ✅ No 1401 errors

---

**Run the diagnostic script first and share the output.**
