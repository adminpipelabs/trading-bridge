# Check Railway Logs for Detailed Error

**Date:** 2026-01-26  
**Issue:** Getting 500 error from Hummingbot API

---

## 🔍 **What to Look For in Railway Logs**

After making the bot creation request, check Railway logs for:

### **1. Request Logging**
```
Making POST request to https://...ngrok.../bot-orchestration/deploy-v2-script with headers: [...]
```

### **2. Error Response**
```
HTTP error 500: {"detail":"..."}
```

The `detail` field will show the actual error message from Hummingbot API.

---

## 📋 **Common 500 Errors**

1. **Credentials profile doesn't exist**
   - Error: `"Credentials profile 'client_sharp' not found"`
   - Fix: Create credentials profile in Hummingbot or use existing one

2. **Script format error**
   - Error: `"Invalid script format"` or syntax error
   - Fix: Check script generation logic

3. **Instance name conflict**
   - Error: `"Instance 'Sharp Spread' already exists"`
   - Fix: Use unique instance names

4. **Missing connector**
   - Error: `"Connector 'bitmart' not configured"`
   - Fix: Configure connector in Hummingbot

---

## 🛠️ **Next Steps**

1. Make bot creation request
2. Check Railway logs immediately after
3. Look for the `HTTP error 500:` line
4. Share the full error message from Hummingbot

---

**The error message will tell us exactly what's wrong!** 🔍
