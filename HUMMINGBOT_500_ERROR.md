# Hummingbot 500 Error - Internal Server Error

**Date:** 2026-01-26  
**Status:** Hummingbot API crashing internally

---

## 🔍 **Error Details**

**Response from Hummingbot:**
- Status: `500 Internal Server Error`
- Content-Type: `text/plain; charset=utf-8`
- Response: `"Internal Server Error"` (21 chars, plain text, no JSON)

**Direct curl test also fails:**
```bash
curl -u admin:admin -H "ngrok-skip-browser-warning: true" \
  -X POST "https://...ngrok.../bot-orchestration/deploy-v2-script" \
  -H "Content-Type: application/json" \
  -d '{"script_content":"test","script_name":"test.py","instance_name":"test","credentials_profile":"test"}'
```

**Result:** `Internal Server Error`

---

## 🐛 **Possible Causes**

1. **Credentials profile doesn't exist**
   - `credentials_profile: "client_sharp"` might not exist in Hummingbot
   - Hummingbot crashes when trying to use non-existent profile

2. **Script format issue**
   - Generated script might have syntax errors
   - Hummingbot can't parse the script

3. **Instance name conflict**
   - Instance name might already exist
   - Hummingbot crashes on duplicate

4. **Hummingbot API bug**
   - Internal error in Hummingbot API code
   - Need to check Hummingbot logs

---

## 📋 **What We Need**

### **1. Check Hummingbot Logs**
Check the local Hummingbot API logs to see the actual error:
```bash
# Check Hummingbot API container logs
docker logs hummingbot-api
```

### **2. Verify Credentials Profile**
We need to know:
- What credentials profiles exist in Hummingbot?
- Does `client_sharp` exist?
- How to create it if it doesn't?

### **3. Test with Minimal Script**
Try deploying a minimal valid script to see if it's a script format issue.

---

## 🛠️ **Next Steps**

1. **Check Hummingbot logs** - See actual error from Hummingbot API
2. **Verify credentials profile** - Check if `client_sharp` exists
3. **Test minimal script** - Try with simplest possible script
4. **Check Hummingbot API docs** - Verify required fields and format

---

## 💡 **Key Finding**

The error is coming from Hummingbot API itself, not our code. The request reaches Hummingbot, but it crashes internally. We need Hummingbot logs to see what's actually failing.

---

**Check Hummingbot API logs to see the real error!** 🔍
