# Production Deployment Checklist

**Use this checklist to ensure proper deployment**

---

## ✅ **Pre-Deployment**

- [ ] Hummingbot API Docker image ready
- [ ] PostgreSQL database plan selected
- [ ] Environment variables documented
- [ ] Service names planned

---

## ✅ **Hummingbot API Deployment**

- [ ] Service created in Railway
- [ ] Service name noted (e.g., `hummingbot-api`)
- [ ] Docker image configured
- [ ] Port set to `8000`
- [ ] Public access: `Off` (internal only)
- [ ] PostgreSQL addon added
- [ ] `DATABASE_URL` set from Postgres addon
- [ ] `HUMMINGBOT_API_USERNAME` set
- [ ] `HUMMINGBOT_API_PASSWORD` set (strong password)
- [ ] Service deployed successfully
- [ ] Logs show "Uvicorn running on http://0.0.0.0:8000"
- [ ] Health check endpoint responding

---

## ✅ **Trading Bridge Configuration**

- [ ] Hummingbot API service name identified
- [ ] `HUMMINGBOT_API_URL` set to `http://[SERVICE_NAME]:8000`
- [ ] `HUMMINGBOT_API_USERNAME` matches Hummingbot API
- [ ] `HUMMINGBOT_API_PASSWORD` matches Hummingbot API
- [ ] `ENVIRONMENT=production` set (optional)
- [ ] Variables saved
- [ ] Service redeployed

---

## ✅ **Verification**

- [ ] Trading Bridge logs show correct URL (not localhost)
- [ ] Trading Bridge logs show "HummingbotClient initialized"
- [ ] `/bots` endpoint returns `{"bots":[]}`
- [ ] No "Configuration Error" in startup logs
- [ ] Bot creation test successful
- [ ] Error messages are clear and helpful

---

## ✅ **Production Readiness**

- [ ] All environment variables set
- [ ] Strong passwords in use
- [ ] Services in same Railway project
- [ ] Internal networking working
- [ ] Logs monitored
- [ ] Error handling tested
- [ ] Documentation updated

---

## 🚨 **Common Issues**

**If checklist incomplete, check:**
- Service name mismatch
- Missing environment variables
- Services in different projects
- Wrong port configuration
- Authentication mismatch

**See `PRODUCTION_DEPLOYMENT.md` for detailed troubleshooting.**

---

**Checklist complete?** ✅ Ready for production!
