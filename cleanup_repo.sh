#!/bin/bash
# Repository Cleanup Script
# Organizes documentation files into proper structure

set -e

echo "=========================================="
echo "REPOSITORY CLEANUP"
echo "=========================================="
echo ""

# Backup first
echo "📦 Step 1: Creating backup commit..."
git add -A
git commit -m "Backup before cleanup - all files preserved" || echo "No changes to commit"
echo "✅ Backup created"
echo ""

# Create directory structure
echo "📁 Step 2: Creating directory structure..."
mkdir -p docs/{deployment,api,reference,archive,guides}
mkdir -p scripts/archive
echo "✅ Directories created"
echo ""

# Move important current docs
echo "📋 Step 3: Organizing important docs..."

# Deployment docs
[ -f "HETZNER_DEPLOYMENT_GUIDE.md" ] && mv HETZNER_DEPLOYMENT_GUIDE.md docs/deployment/
[ -f "RAILWAY_STATIC_IP_UPDATE.md" ] && mv RAILWAY_STATIC_IP_UPDATE.md docs/deployment/
[ -f "DEPLOYMENT_CHECKLIST.md" ] && mv DEPLOYMENT_CHECKLIST.md docs/deployment/
[ -f "deploy_hetzner.sh" ] && mv deploy_hetzner.sh scripts/

# API/Exchange docs
[ -f "IP_WHITELIST_REQUIREMENTS.md" ] && mv IP_WHITELIST_REQUIREMENTS.md docs/api/
[ -f "VOLUME_BOT_MARKET_ORDER_UPGRADE.md" ] && mv VOLUME_BOT_MARKET_ORDER_UPGRADE.md docs/api/
[ -f "COMPARE_WITH_COINOPTIMUS.md" ] && mv COMPARE_WITH_COINOPTIMUS.md docs/reference/
[ -f "COINSTORE_OFFICIAL_DOCS_ANALYSIS.md" ] && mv COINSTORE_OFFICIAL_DOCS_ANALYSIS.md docs/reference/

# Current guides
[ -f "LAUNCH_PREPARATION_CHECKLIST.md" ] && mv LAUNCH_PREPARATION_CHECKLIST.md docs/guides/
[ -f "REPO_CLEANUP_PLAN.md" ] && mv REPO_CLEANUP_PLAN.md docs/guides/
[ -f "HETZNER_FIX_CHECKLIST.md" ] && mv HETZNER_FIX_CHECKLIST.md docs/guides/
[ -f "IP_WHITELIST_CHECKLIST.md" ] && mv IP_WHITELIST_CHECKLIST.md docs/guides/

echo "✅ Important docs organized"
echo ""

# Archive old status/fix docs
echo "📦 Step 4: Archiving old docs..."

# Status docs
find . -maxdepth 1 -name "*_STATUS*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "STATUS*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "CURRENT_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true

# Fix docs
find . -maxdepth 1 -name "*_FIX*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "FIX_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true

# Summary docs
find . -maxdepth 1 -name "*_SUMMARY*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "SUMMARY*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true

# Urgent docs
find . -maxdepth 1 -name "URGENT_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true

# Dev/CTO messages
find . -maxdepth 1 -name "*_FOR_DEV*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_FOR_CTO*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "DEV_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "ASK_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "MESSAGE_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true

# Debug/Test docs
find . -maxdepth 1 -name "DEBUG_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "TEST_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "CHECK_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true

# Other old docs
find . -maxdepth 1 -name "QUICK_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "FINAL_*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "PHASE*.md" -type f -exec mv {} docs/archive/ \; 2>/dev/null || true

echo "✅ Old docs archived"
echo ""

# Archive old scripts
echo "📦 Step 5: Archiving old scripts..."
find . -maxdepth 1 -name "fix_*.sh" -type f -exec mv {} scripts/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "check_*.py" -type f -exec mv {} scripts/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "test_*.py" -type f -exec mv {} scripts/archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*.sql" -type f -exec mv {} scripts/archive/ \; 2>/dev/null || true
echo "✅ Old scripts archived"
echo ""

# Create README for docs
echo "📝 Step 6: Creating docs README..."
cat > docs/README.md << 'EOF'
# Documentation

## 📁 Structure

- **deployment/** - Deployment guides and setup instructions
- **api/** - API and exchange integration docs
- **reference/** - Reference documentation and comparisons
- **guides/** - Step-by-step guides and checklists
- **archive/** - Historical status updates and old fixes

## 🚀 Quick Links

### Current Guides
- [Launch Preparation Checklist](../docs/guides/LAUNCH_PREPARATION_CHECKLIST.md)
- [IP Whitelist Requirements](../docs/api/IP_WHITELIST_REQUIREMENTS.md)
- [Hetzner Deployment Guide](../docs/deployment/HETZNER_DEPLOYMENT_GUIDE.md)

### Reference
- [Coinstore Implementation Comparison](../docs/reference/COMPARE_WITH_COINOPTIMUS.md)
- [Volume Bot Market Order Upgrade](../docs/api/VOLUME_BOT_MARKET_ORDER_UPGRADE.md)
EOF

echo "✅ Docs README created"
echo ""

# Summary
echo "=========================================="
echo "CLEANUP COMPLETE"
echo "=========================================="
echo ""
echo "📊 Summary:"
echo "  - Important docs → docs/{deployment,api,reference,guides}/"
echo "  - Old docs → docs/archive/"
echo "  - Old scripts → scripts/archive/"
echo ""
echo "📝 Next steps:"
echo "  1. Review changes: git status"
echo "  2. Commit: git add -A && git commit -m 'Organize repository structure'"
echo "  3. Push: git push"
echo ""
echo "✅ Repository is now organized!"
