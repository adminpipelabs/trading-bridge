# Find Service Name - Step by Step Guide

**Let's check multiple places systematically**

---

## 🔍 **METHOD 1: Check Project Overview**

### **Step 1:**
1. **Click on your project name** (top left of Railway dashboard)
2. **OR go to:** https://railway.app/dashboard
3. **Select your project**

### **Step 2:**
**Look at the list of services** - you should see:
- Trading Bridge
- Hummingbot API (or similar name)
- Postgres

### **Step 3:**
**What is the name shown for Hummingbot API service?**

**Tell me:** What name do you see? (e.g., "hummingbot-api", "hummingbot", etc.)

---

## 🔍 **METHOD 2: Check URL**

### **Step 1:**
**Look at your browser URL bar** when you're on the Hummingbot API service page

**Format might be:**
```
https://railway.app/project/<project-id>/service/<service-id>
```

### **Step 2:**
**OR check the page title/tab name**

**What does it say?**

---

## 🔍 **METHOD 3: Check Variables Tab**

### **Step 1:**
1. **In Hummingbot API service**
2. **Click "Variables" tab**

### **Step 2:**
**Look for these variables:**
- `RAILWAY_SERVICE_NAME`
- `RAILWAY_SERVICE_ID`
- Any variable with "SERVICE" in the name

### **Step 3:**
**Scroll through all variables** - Railway might have auto-generated variables

**What variables do you see?**

---

## 🔍 **METHOD 4: Check Settings Tab**

### **Step 1:**
1. **In Hummingbot API service**
2. **Click "Settings" tab** (not Networking)

### **Step 2:**
**Look for:**
- Service Name
- Service ID
- Display Name
- Any name field

**What do you see?**

---

## 🔍 **METHOD 5: Check Deployments Tab**

### **Step 1:**
1. **In Hummingbot API service**
2. **Click "Deployments" tab**

### **Step 2:**
**Look at deployment logs** - might show service name

**What do you see in the logs?**

---

## 🎯 **ALTERNATIVE: Use Default Name**

**If we can't find it, we can try common names:**

1. **Try:** `hummingbot-api`
2. **Try:** `hummingbot`
3. **Try:** Check what you named it when creating

**Then test if it works!**

---

## ✅ **What to Do**

**Please check these in order:**

1. **Project overview** - What's the service called?
2. **Variables tab** - Any SERVICE_NAME variable?
3. **Settings tab** - Any name field?
4. **Browser URL** - What's in the URL?

**OR just tell me:**
- What did you name it when you created it?
- Or try: `hummingbot-api` (most common)

---

**Let's start with Method 1 - check your project overview and tell me what the Hummingbot service is called!** 🔍
