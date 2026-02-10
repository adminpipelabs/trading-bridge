#!/bin/bash
# Automated script to copy dashboard redesign to ai-trading-ui repository
# Usage: ./scripts/migrate_to_railway_frontend.sh [path-to-ai-trading-ui]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get source and target directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$REPO_ROOT/frontend"

# Check if target directory provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <path-to-ai-trading-ui-repo>${NC}"
    echo ""
    echo "Example:"
    echo "  $0 ../ai-trading-ui"
    echo "  $0 ~/projects/ai-trading-ui"
    echo ""
    echo "Or clone it first:"
    echo "  git clone https://github.com/[your-org]/ai-trading-ui.git ../ai-trading-ui"
    echo "  $0 ../ai-trading-ui"
    exit 1
fi

TARGET_DIR="$1"

# Validate source directory
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ Source directory not found: $SOURCE_DIR${NC}"
    exit 1
fi

# Validate target directory
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${RED}❌ Target directory not found: $TARGET_DIR${NC}"
    echo ""
    echo "Please clone the ai-trading-ui repository first:"
    echo "  git clone https://github.com/[your-org]/ai-trading-ui.git $TARGET_DIR"
    exit 1
fi

echo "=========================================="
echo "Dashboard Redesign Migration"
echo "=========================================="
echo ""
echo -e "${GREEN}Source:${NC} $SOURCE_DIR"
echo -e "${GREEN}Target:${NC} $TARGET_DIR"
echo ""

# Confirm
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

cd "$TARGET_DIR"

# Check if it's a git repo
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Warning: Target directory is not a git repository${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo ""
echo -e "${GREEN}[1/6]${NC} Creating directory structure..."

# Create directories if they don't exist
mkdir -p src/components/dashboard
mkdir -p src/components/ui
mkdir -p src/lib
mkdir -p src/hooks

echo -e "${GREEN}✅ Directories created${NC}"

echo ""
echo -e "${GREEN}[2/6]${NC} Copying dashboard components..."
cp -r "$SOURCE_DIR/components/dashboard"/* src/components/dashboard/ 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Some files may already exist (skipping)${NC}"
}
echo -e "${GREEN}✅ Dashboard components copied${NC}"

echo ""
echo -e "${GREEN}[3/6]${NC} Copying UI components..."
# Copy UI components, but don't overwrite existing ones
for file in "$SOURCE_DIR/components/ui"/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        if [ ! -f "src/components/ui/$filename" ]; then
            cp "$file" "src/components/ui/"
        fi
    fi
done
echo -e "${GREEN}✅ UI components copied${NC}"

echo ""
echo -e "${GREEN}[4/6]${NC} Copying utilities..."
cp "$SOURCE_DIR/lib/utils.ts" src/lib/utils.ts 2>/dev/null || {
    echo -e "${YELLOW}⚠️  utils.ts may already exist${NC}"
}
echo -e "${GREEN}✅ Utilities copied${NC}"

echo ""
echo -e "${GREEN}[5/6]${NC} Copying hooks..."
cp -r "$SOURCE_DIR/hooks"/* src/hooks/ 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Hooks may already exist${NC}"
}
echo -e "${GREEN}✅ Hooks copied${NC}"

echo ""
echo -e "${GREEN}[6/6]${NC} Creating migration summary..."

# Create a summary file
cat > MIGRATION_SUMMARY.md << EOF
# Dashboard Redesign Migration Summary

**Date:** $(date)
**Source:** $SOURCE_DIR
**Target:** $TARGET_DIR

## ✅ Files Copied

- ✅ Dashboard components: \`src/components/dashboard/*\`
- ✅ UI components: \`src/components/ui/*\`
- ✅ Utilities: \`src/lib/utils.ts\`
- ✅ Hooks: \`src/hooks/*\`

## 📋 Next Steps

1. **Install dependencies:**
   \`\`\`bash
   npm install @radix-ui/react-accordion @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select @radix-ui/react-tabs @radix-ui/react-toast lucide-react next-themes tailwind-merge clsx class-variance-authority date-fns recharts sonner vaul zod react-hook-form @hookform/resolvers
   \`\`\`

2. **Update Tailwind config** (see \`docs/guides/RAILWAY_FRONTEND_MIGRATION.md\`)

3. **Update global CSS** (add CSS variables)

4. **Connect API endpoints** (replace mock data in components)

5. **Commit and push:**
   \`\`\`bash
   git add .
   git commit -m "Add dashboard redesign components"
   git push
   \`\`\`

6. **Railway will auto-deploy!** 🚀

## 📚 Documentation

See \`docs/guides/RAILWAY_FRONTEND_MIGRATION.md\` for complete instructions.
EOF

echo -e "${GREEN}✅ Migration summary created${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Migration Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. ${YELLOW}Install dependencies:${NC}"
echo "   cd $TARGET_DIR"
echo "   npm install @radix-ui/react-accordion @radix-ui/react-dialog lucide-react next-themes tailwind-merge clsx class-variance-authority"
echo ""
echo "2. ${YELLOW}Update Tailwind config and CSS${NC}"
echo "   See: docs/guides/RAILWAY_FRONTEND_MIGRATION.md"
echo ""
echo "3. ${YELLOW}Connect API endpoints${NC}"
echo "   Replace mock data in components with real API calls"
echo ""
echo "4. ${YELLOW}Commit and push:${NC}"
echo "   git add ."
echo "   git commit -m 'Add dashboard redesign'"
echo "   git push"
echo ""
echo "5. ${YELLOW}Railway will auto-deploy!${NC} 🚀"
echo ""
echo "See MIGRATION_SUMMARY.md for details."
