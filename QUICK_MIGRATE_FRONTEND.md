# Quick Frontend Migration Guide

**Goal:** Copy dashboard redesign to Railway `ai-trading-ui` repository

---

## 🚀 **Option 1: Automated Script (Recommended)**

```bash
# 1. Clone your ai-trading-ui repo (if not already cloned)
git clone https://github.com/[your-org]/ai-trading-ui.git ../ai-trading-ui

# 2. Run migration script
./scripts/migrate_to_railway_frontend.sh ../ai-trading-ui

# 3. Follow the prompts and next steps
```

---

## 📋 **Option 2: Manual Steps**

### **Step 1: Clone ai-trading-ui**
```bash
git clone https://github.com/[your-org]/ai-trading-ui.git
cd ai-trading-ui
```

### **Step 2: Copy Components**
```bash
# From trading-bridge directory
cp -r frontend/components/dashboard ai-trading-ui/src/components/
cp -r frontend/components/ui ai-trading-ui/src/components/
cp frontend/lib/utils.ts ai-trading-ui/src/lib/
cp -r frontend/hooks ai-trading-ui/src/
```

### **Step 3: Install Dependencies**
```bash
cd ai-trading-ui
npm install @radix-ui/react-accordion @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select @radix-ui/react-tabs @radix-ui/react-toast lucide-react next-themes tailwind-merge clsx class-variance-authority date-fns recharts sonner vaul zod react-hook-form @hookform/resolvers
```

### **Step 4: Update Config Files**
- Update `tailwind.config.js` (see `docs/guides/RAILWAY_FRONTEND_MIGRATION.md`)
- Update global CSS with CSS variables
- Connect API endpoints in components

### **Step 5: Commit & Push**
```bash
git add .
git commit -m "Add dashboard redesign"
git push
```

**Railway auto-deploys!** ✅

---

## 📚 **Full Guide**

See `docs/guides/RAILWAY_FRONTEND_MIGRATION.md` for complete instructions.

---

**Ready to migrate!** 🚀
