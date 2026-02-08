# Check Browser Console Debug Logs

**Steps:**
1. Open browser (Chrome/Safari/Firefox)
2. Open DevTools (F12 or Cmd+Option+I on Mac)
3. Go to **Console** tab
4. Click "Start Bot" button
5. Look for DEBUG logs

---

## What to Look For

### ✅ **If you see these logs (in order):**

```
DEBUG: handleStartStop called {botId: "...", action: "start"}
DEBUG: botId type: string
DEBUG: botId value: 74d9b480-f15b-444d-a290-a798b59c584a
DEBUG: API_BASE: https://trading-bridge-production.up.railway.app
DEBUG: Starting bot, URL: https://trading-bridge-production.up.railway.app/bots/74d9b480-f15b-444d-a290-a798b59c584a/start
DEBUG: About to call fetch...
```

**Then:** The code is running correctly. The error happens during `fetch()` call.

**Next:** Check **Network** tab to see what the actual HTTP error is (CORS, 401, 500, etc.)

---

### ❌ **If you see NO DEBUG logs at all:**

**Problem:** Click handler isn't running or JavaScript error on page load.

**Check:**
1. Are there any **red errors** in Console?
2. Is the button wired correctly? Check HTML:
   ```html
   <button onClick={() => handleStartStop(bot.id, 'start')}>
   ```
3. Is `ClientDashboard.jsx` loaded? Check Sources tab.

---

### ⚠️ **If you see partial logs:**

**Example:** Only see `DEBUG: handleStartStop called` but nothing after:

```
DEBUG: handleStartStop called {botId: "...", action: "start"}
[ERROR] Cannot read property 'startBot' of undefined
```

**Problem:** `tradingBridge` object is undefined or `startBot` function missing.

**Check:**
- Is `tradingBridge` imported correctly?
- Is `api.js` loaded?

---

### 🔍 **If you see error before fetch:**

**Example:**
```
DEBUG: Starting bot, URL: ...
DEBUG: Fetch error: TypeError: Failed to construct 'Request'
```

**Problem:** Invalid URL or headers causing fetch to fail before network request.

**Check:**
- Is `TRADING_BRIDGE_URL` set correctly?
- Are headers valid?

---

## Expected Debug Log Sequence

**Full successful flow should show:**

1. `DEBUG: handleStartStop called` ← Button click detected
2. `DEBUG: botId type: string` ← BotId is valid
3. `DEBUG: botId value: ...` ← BotId value
4. `DEBUG: API_BASE: ...` ← URL is set
5. `DEBUG: Starting bot, URL: ...` ← About to call API
6. `DEBUG: About to call fetch...` ← Fetch starting
7. **[Network request appears in Network tab]**

**If it stops at step 1-4:** Code error before fetch
**If it stops at step 5-6:** Fetch configuration issue
**If it reaches step 7:** Backend/network issue (check Network tab)

---

## Screenshot What You See

**Please screenshot:**
1. **Console tab** - All DEBUG logs and any errors
2. **Network tab** - The failed request (if it appears)
   - Click on the failed request
   - Show: Status code, Headers, Response

---

## Quick Test

**If no DEBUG logs appear, test if JavaScript is working:**

Open Console and type:
```javascript
console.log('Test');
```

If this doesn't appear, Console isn't working. Try:
- Refresh page
- Clear cache
- Try different browser
