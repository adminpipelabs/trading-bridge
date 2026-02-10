# Final Fix Plan - Get Coinstore Working

**Goal:** Get bots running and balance showing

---

## 🎯 **What We Know**

- ✅ Code matches official Coinstore docs exactly
- ✅ Hetzner deployed and running
- ✅ IP 5.161.64.209 whitelisted (you said)
- ❌ Still 1401 Unauthorized

---

## 🔧 **Run This on Hetzner**

```bash
cd /opt/trading-bridge
source venv/bin/activate
bash diagnose_and_fix_coinstore.sh
```

**This will:**
1. Load credentials from database
2. Test Coinstore API with exact official method
3. Show full response
4. Tell you exactly what's wrong

---

## ✅ **What to Check**

**After running the script, check:**

1. **If 1401 error:**
   - Coinstore dashboard → API Key `42b5c7c40bf625e7fcffd16a654b6ed0`
   - Is IP `5.161.64.209` actually in the IP binding list?
   - Does API secret match what script shows?

2. **If success:**
   - Check bot logs: `journalctl -u trading-bridge -f`
   - Should see balance and orders

---

**Run the script and share the output. I'll tell you exactly what to fix.**
