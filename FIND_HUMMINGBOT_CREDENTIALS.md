# How to Find Hummingbot API Credentials

**Need to find the correct username and password for Hummingbot API**

---

## 🔍 **Method 1: Check Hummingbot Configuration Files**

### **Look for config files:**

```bash
# Check Hummingbot directory
ls ~/hummingbot_files/

# Look for config files
cat ~/hummingbot_files/conf/global_conf.yml | grep -i "api\|username\|password"
cat ~/hummingbot_files/conf/conf_api.yml | grep -i "username\|password"
```

---

## 🔍 **Method 2: Check Environment Variables**

### **If using Docker:**

```bash
# Check docker-compose.yml
cat ~/hummingbot_files/docker-compose.yml | grep -i "HUMMINGBOT\|API\|USERNAME\|PASSWORD"

# Or check running container
docker exec hummingbot-api env | grep -i "API\|USERNAME\|PASSWORD"
```

---

## 🔍 **Method 3: Check Hummingbot API Logs**

### **Look at API startup logs:**

```bash
# Check Hummingbot API logs
docker logs hummingbot-api | grep -i "username\|password\|auth"

# Or if running directly
# Check logs for authentication setup
```

---

## 🔍 **Method 4: Check Default Credentials**

### **Hummingbot API common defaults:**

**Username:**
- `hummingbot` (most common)
- `admin`
- `user`

**Password:**
- Check your Hummingbot setup/config
- May be in `.env` file
- May be set during initial setup

---

## 🔍 **Method 5: Check .env File**

### **Look for environment file:**

```bash
# Check for .env file
cat ~/hummingbot_files/.env | grep -i "API\|USERNAME\|PASSWORD"

# Or check inside container
docker exec hummingbot-api cat /app/.env | grep -i "API\|USERNAME\|PASSWORD"
```

---

## 🔍 **Method 6: Test Common Credentials**

### **Try common combinations:**

1. **Username:** `hummingbot`, **Password:** (check config)
2. **Username:** `admin`, **Password:** (check config)
3. **Username:** `user`, **Password:** (check config)

---

## 🔍 **Method 7: Check Hummingbot Documentation**

### **Check Hummingbot docs:**

- Look for API authentication section
- Check setup guide
- Check configuration documentation

---

## 🎯 **Quick Check Commands**

**Run these to find credentials:**

```bash
# Check docker-compose.yml
cat ~/hummingbot_files/docker-compose.yml | grep -A 10 "hummingbot-api"

# Check environment variables
docker exec hummingbot-api env | grep -i "API"

# Check config files
find ~/hummingbot_files -name "*.yml" -o -name "*.yaml" | xargs grep -i "username\|password" 2>/dev/null

# Check .env file
cat ~/hummingbot_files/.env 2>/dev/null | grep -i "API\|USERNAME\|PASSWORD"
```

---

## 📋 **What to Look For**

**Common variable names:**
- `HUMMINGBOT_API_USERNAME`
- `HUMMINGBOT_API_PASSWORD`
- `API_USERNAME`
- `API_PASSWORD`
- `AUTH_USERNAME`
- `AUTH_PASSWORD`

---

## ✅ **Once You Find It**

**Update Railway variables:**
1. Railway Dashboard → Trading Bridge
2. Variables tab
3. Update `HUMMINGBOT_API_USERNAME`
4. Update `HUMMINGBOT_API_PASSWORD`
5. Save

---

**Try these methods to find your Hummingbot API credentials!** 🔍
