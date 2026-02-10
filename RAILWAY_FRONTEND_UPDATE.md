# Railway Frontend Update - Quick Reference

**Action:** Copy dashboard redesign to `ai-trading-ui` repository  
**Status:** Ready to deploy

---

## 🚀 **Quick Steps**

1. **Clone ai-trading-ui repo:**
   ```bash
   git clone https://github.com/[your-org]/ai-trading-ui.git
   cd ai-trading-ui
   ```

2. **Copy components from trading-bridge:**
   ```bash
   # Copy dashboard components
   cp -r ../trading-bridge/frontend/components/dashboard src/components/
   cp -r ../trading-bridge/frontend/components/ui src/components/
   cp -r ../trading-bridge/frontend/lib src/
   ```

3. **Install dependencies:**
   ```bash
   npm install @radix-ui/react-accordion @radix-ui/react-dialog lucide-react next-themes tailwind-merge clsx class-variance-authority
   # ... (see full list in RAILWAY_FRONTEND_MIGRATION.md)
   ```

4. **Update Tailwind config** (merge with existing)

5. **Connect API endpoints** (replace mock data)

6. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add dashboard redesign"
   git push
   ```

7. **Railway auto-deploys!** ✅

---

## 📋 **Full Guide**

See `docs/guides/RAILWAY_FRONTEND_MIGRATION.md` for complete step-by-step instructions.

---

**The redesign is ready - just copy to ai-trading-ui and Railway will handle the rest!**
