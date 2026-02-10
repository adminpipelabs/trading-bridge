# Final Coinstore Fix - Get Bots Working

**Goal:** Get Coinstore bots running and showing balance

---

## 🎯 **The Issue**

- Hetzner deployed ✅
- App running ✅
- Still 1401 from Coinstore ❌

**This means:** Coinstore credentials/IP whitelist issue

---

## 🔧 **Run This on Hetzner**

```bash
cd /opt/trading-bridge
bash fix_coinstore_now.sh
```

**This will:**
1. Show credentials from database
2. Test Coinstore API
3. Show bot logs
4. Tell you exactly what to check

---

## ✅ **What to Verify**

**On Coinstore Dashboard:**

1. **API Key:** `42b5c7c40bf625e7fcffd16a654b6ed0`
2. **IP Whitelist:** Is `5.161.64.209` listed?
3. **API Secret:** Does it match database?
4. **Permissions:** Read + Trade enabled?

---

## 🚀 **If IP Not Whitelisted**

1. Coinstore dashboard → API settings
2. Find key `42b5c7c40bf625e7fcffd16a654b6ed0`
3. Add IP: `5.161.64.209`
4. Save
5. Wait 1-2 minutes
6. Restart service: `systemctl restart trading-bridge`

---

## 🚀 **If Secret Wrong**

Update database with correct secret, then restart service.

---

**Run the script and share output. We'll fix it.**
