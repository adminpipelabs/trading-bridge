# Check Railway Logs - Quick Guide

**Status:** Getting Internal Server Error  
**Need:** Check logs to see actual error

---

## 🔍 **Step 1: Check Trading Bridge Logs**

### **Action:**

1. **Go to Railway Dashboard**
2. **Your Project** → **Trading Bridge** service
3. **Click "Logs" tab** (or "Deployments" → Latest → "View Logs")

### **Look for:**

**Search for these keywords:**
- `HummingbotClient`
- `Connection`
- `Error`
- `Failed`
- `refused`
- `resolve`

**What error message do you see?**

---

## 🎯 **Common Errors You Might See**

### **Error 1:**
```
Name resolution failed: hummingbot-api
```
**Meaning:** Wrong service name  
**Fix:** Need to find correct service name

### **Error 2:**
```
Connection refused
```
**Meaning:** Can't reach Hummingbot API  
**Fix:** Check Hummingbot API is running

### **Error 3:**
```
Not authenticated
```
**Meaning:** Wrong credentials  
**Fix:** Check username/password

---

## 📋 **What to Do**

**Option A: Share the Error**
- Copy the error message from logs
- Share it with me
- I'll help fix it

**Option B: Try Different Service Name**
- Change `HUMMINGBOT_API_URL` to try:
  - `http://hummingbot:8000` (without -api)
  - Or check what Railway actually named it

---

## 🔍 **Alternative: Check Service Name**

**To find the actual service name:**

1. **Go to Railway project overview**
2. **Look at list of services**
3. **What is Hummingbot API service called?**

**Common names:**
- `hummingbot-api`
- `hummingbot`
- `service-xxxxx` (auto-generated)

---

## ✅ **Quick Action**

**Please:**
1. **Check Trading Bridge logs**
2. **Find the error message**
3. **Share it with me**

**OR**

**Tell me:**
- What is the Hummingbot API service called in your project list?

**Then I can help fix it!** 🔧
