# Repository Cleanup Plan

**Goal:** Organize and clean up documentation files

---

## 📊 **Current State**

**Problem:**
- 100+ markdown files in root directory
- Many outdated status/fix documents
- Hard to find important information
- Cluttered repository

---

## 🎯 **Cleanup Strategy**

### **Keep (Important Docs):**
- `README.md` - Main readme
- `LAUNCH_PREPARATION_CHECKLIST.md` - Current launch prep
- `IP_WHITELIST_REQUIREMENTS.md` - Current IP whitelist info
- `RAILWAY_STATIC_IP_UPDATE.md` - Railway static IP info
- `VOLUME_BOT_MARKET_ORDER_UPGRADE.md` - Recent upgrade docs
- `COMPARE_WITH_COINOPTIMUS.md` - Code comparison
- `HETZNER_DEPLOYMENT_GUIDE.md` - Deployment guide
- `deploy_hetzner.sh` - Deployment script

### **Archive (Old Status/Fix Docs):**
Move to `docs/archive/`:
- All `*_STATUS.md` files (old status updates)
- All `*_FIX*.md` files (old fixes)
- All `*_SUMMARY*.md` files (old summaries)
- All `URGENT_*.md` files (old urgent fixes)
- All `*_FOR_DEV*.md` files (old dev messages)
- All `*_FOR_CTO*.md` files (old CTO messages)

### **Delete (Temporary/Test Files):**
- `test_*.py` files (if not needed)
- `check_*.py` files (diagnostic scripts)
- `fix_*.sh` files (one-time fix scripts)
- `*.sql` files (one-time SQL scripts)

---

## 📁 **Proposed Structure**

```
trading-bridge/
├── README.md
├── docs/
│   ├── deployment/
│   │   ├── HETZNER_DEPLOYMENT_GUIDE.md
│   │   └── RAILWAY_STATIC_IP_UPDATE.md
│   ├── api/
│   │   ├── IP_WHITELIST_REQUIREMENTS.md
│   │   └── VOLUME_BOT_MARKET_ORDER_UPGRADE.md
│   ├── reference/
│   │   └── COMPARE_WITH_COINOPTIMUS.md
│   └── archive/
│       └── [all old status/fix docs]
├── scripts/
│   ├── deploy_hetzner.sh
│   └── [other scripts]
└── app/
    └── [code]
```

---

## ✅ **Cleanup Steps**

1. **Create docs structure:**
   ```bash
   mkdir -p docs/{deployment,api,reference,archive}
   ```

2. **Move important docs:**
   ```bash
   mv HETZNER_DEPLOYMENT_GUIDE.md docs/deployment/
   mv RAILWAY_STATIC_IP_UPDATE.md docs/deployment/
   mv IP_WHITELIST_REQUIREMENTS.md docs/api/
   mv VOLUME_BOT_MARKET_ORDER_UPGRADE.md docs/api/
   mv COMPARE_WITH_COINOPTIMUS.md docs/reference/
   ```

3. **Archive old docs:**
   ```bash
   mv *_STATUS.md docs/archive/ 2>/dev/null || true
   mv *_FIX*.md docs/archive/ 2>/dev/null || true
   mv *_SUMMARY*.md docs/archive/ 2>/dev/null || true
   mv URGENT_*.md docs/archive/ 2>/dev/null || true
   mv *_FOR_DEV*.md docs/archive/ 2>/dev/null || true
   mv *_FOR_CTO*.md docs/archive/ 2>/dev/null || true
   ```

4. **Delete temporary files:**
   ```bash
   rm -f test_*.py check_*.py fix_*.sh *.sql
   ```

5. **Update README.md:**
   - Add links to important docs
   - Remove outdated info

---

## 🎯 **Quick Cleanup (Minimal)**

**Just organize the most important:**

1. Keep only current docs in root
2. Move everything else to `docs/archive/`
3. Update README with links

---

## ⚠️ **Before Cleanup**

**Backup first:**
```bash
git add -A
git commit -m "Before cleanup - backup all files"
git push
```

**Then cleanup:**
- Can always restore from git history
- Archive folder preserves everything

---

**Should I create a cleanup script to do this automatically?**
