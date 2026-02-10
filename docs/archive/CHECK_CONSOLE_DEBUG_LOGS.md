# Check Browser Console for DEBUG Logs

**After clicking "Start Bot", check Console tab for these logs:**

---

## ✅ **Expected DEBUG Log Sequence**

**1. handleStartStop logs:**
```
DEBUG: handleStartStop called {botId: "...", action: "start"}
DEBUG: About to call tradingBridge.startBot/stopBot
DEBUG: botId type: string
DEBUG: botId value: 74d9b480-f15b-444d-a290-a798b59c584a
DEBUG: API_BASE: https://trading-bridge-production.up.railway.app
```

**2. startBot logs:**
```
DEBUG: startBot called {botId: "74d9b480-f15b-444d-a290-a798b59c584a"}
DEBUG: TRADING_BRIDGE_URL: https://trading-bridge-production.up.railway.app
DEBUG: Starting bot, URL: https://trading-bridge-production.up.railway.app/bots/74d9b480-f15b-444d-a290-a798b59c584a/start
DEBUG: About to call apiCall...
```

**3. apiCall logs (from apiCall wrapper):**
```
🔍 API Call to /bots: {
  url: "https://trading-bridge-production.up.railway.app/bots/.../start",
  method: "POST",
  hasWalletAddress: true,
  walletAddress: "74d9b480...",
  hasToken: true/false,
  headers: ["Content-Type", "Authorization", "X-Wallet-Address"]
}
```

**4. Fetch response logs:**
```
📥 Fetch response: {
  url: "...",
  status: 200/401/404/500,
  statusText: "OK",
  ok: true/false
}
```

**5. Success or Error:**
```
DEBUG: startBot succeeded: {...}
```
OR
```
DEBUG: startBot failed: Error: ...
DEBUG: Error message: ...
DEBUG: Error name: ...
```

---

## ❌ **If NO DEBUG Logs Appear**

**Problem:** Code crashes before reaching `handleStartStop`

**Check:**
1. Are there any **red errors** in Console?
2. Is the button wired correctly? Check React DevTools
3. Is JavaScript enabled?
4. Are there any syntax errors in the page?

---

## ⚠️ **If Partial DEBUG Logs**

**Example: Only see `handleStartStop` logs but not `startBot` logs:**

```
DEBUG: handleStartStop called {botId: "...", action: "start"}
DEBUG: About to call tradingBridge.startBot/stopBot
[ERROR] Cannot read property 'startBot' of undefined
```

**Problem:** `tradingBridge` object is undefined or not imported correctly.

---

## 🔍 **What to Report**

**Screenshot the Console tab showing:**
1. All DEBUG logs (if any)
2. Any red error messages
3. The exact sequence of logs

**Or copy/paste the console output.**

---

## 📋 **Quick Test**

**Open Console and type:**
```javascript
console.log('Test');
```

If this doesn't appear, Console isn't working. Try:
- Refresh page
- Clear cache
- Try different browser

---

**After clicking "Start Bot", screenshot the Console tab and share what you see!**
