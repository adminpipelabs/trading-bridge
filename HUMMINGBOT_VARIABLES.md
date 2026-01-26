# Hummingbot API - Environment Variables

**Service:** Hummingbot API (Railway)  
**Step:** Set environment variables

---

## 📋 **Variables to Add**

### **Step 1: API Authentication** (Required)

Add these first:

```bash
USERNAME=admin
PASSWORD=admin
CONFIG_PASSWORD=admin
```

**Where:** Hummingbot API service → Variables tab → Add each one

---

### **Step 2: Database** (Required)

**First, get Postgres connection string:**

1. Go to **Postgres** service (in same project)
2. **Variables** tab
3. Find `DATABASE_URL` or `POSTGRES_URL`
4. Copy it

**Then convert it:**

**Railway gives you:**
```
postgresql://postgres:password@host:port/dbname
```

**Change to (add +asyncpg):**
```
postgresql+asyncpg://postgres:password@host:port/dbname
```

**Add variable:**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@host:port/dbname
```

**Replace with your actual Postgres URL!**

---

### **Step 3: Broker** (Optional - Can Skip for Now)

```bash
BROKER_HOST=localhost
BROKER_USERNAME=admin
BROKER_PASSWORD=password
```

**Note:** These are optional. Hummingbot API may work without broker for basic functionality.

---

### **Step 4: Gateway** (Optional - Can Skip for Now)

```bash
GATEWAY_PASSPHRASE=admin
```

**Note:** Optional, can skip if not using gateway features.

---

### **Step 5: Paths** (Required)

```bash
BOTS_PATH=/app/bots
```

---

## ✅ **Minimum Required Variables**

**If you want to start simple, add these 4:**

```bash
USERNAME=admin
PASSWORD=admin
CONFIG_PASSWORD=admin
DATABASE_URL=postgresql+asyncpg://postgres:password@host:port/dbname
BOTS_PATH=/app/bots
```

**Then add broker/gateway later if needed.**

---

## 📝 **Step-by-Step Instructions**

### **1. Go to Hummingbot API Service**

Railway Dashboard → Your Project → Hummingbot API service

### **2. Open Variables Tab**

Click **Variables** tab

### **3. Add Variables One by One**

Click **+ New Variable** for each:

**Variable 1:**
- Name: `USERNAME`
- Value: `admin`
- Click **Add**

**Variable 2:**
- Name: `PASSWORD`
- Value: `admin`
- Click **Add**

**Variable 3:**
- Name: `CONFIG_PASSWORD`
- Value: `admin`
- Click **Add**

**Variable 4:**
- Name: `DATABASE_URL`
- Value: `postgresql+asyncpg://...` (your Postgres URL with +asyncpg)
- Click **Add**

**Variable 5:**
- Name: `BOTS_PATH`
- Value: `/app/bots`
- Click **Add**

---

## 🔍 **How to Get Postgres URL**

**If you haven't added Postgres yet:**

1. Go to Railway project
2. Click **+ New** → **Database** → **Add Postgres**
3. Wait for deployment
4. Click on **Postgres** service
5. **Variables** tab
6. Copy `DATABASE_URL`

**If Postgres already exists:**

1. Click on **Postgres** service
2. **Variables** tab
3. Copy `DATABASE_URL`
4. Add `+asyncpg` after `postgresql`

---

## ⚠️ **Important Notes**

1. **DATABASE_URL format:**
   - Must have `+asyncpg` for Hummingbot
   - Format: `postgresql+asyncpg://user:pass@host:port/dbname`

2. **Railway will auto-deploy** when you add variables
   - Watch the **Deployments** tab
   - Check **Logs** for any errors

3. **If deployment fails:**
   - Check logs for error messages
   - Verify DATABASE_URL format
   - Make sure Postgres is running

---

## ✅ **Checklist**

- [ ] USERNAME=admin added
- [ ] PASSWORD=admin added
- [ ] CONFIG_PASSWORD=admin added
- [ ] Postgres added to project
- [ ] DATABASE_URL copied from Postgres
- [ ] DATABASE_URL has +asyncpg
- [ ] DATABASE_URL added to Hummingbot API
- [ ] BOTS_PATH=/app/bots added
- [ ] Railway deploying (check Deployments tab)

---

## 🎯 **Quick Copy-Paste**

**Minimum required (if Postgres already added):**

```bash
USERNAME=admin
PASSWORD=admin
CONFIG_PASSWORD=admin
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DB
BOTS_PATH=/app/bots
```

**Replace YOUR_PASSWORD, YOUR_HOST, YOUR_DB with actual values from Railway Postgres!**

---

**Ready to add variables?** 🚀

**Start with USERNAME, PASSWORD, CONFIG_PASSWORD first, then get Postgres URL!**
