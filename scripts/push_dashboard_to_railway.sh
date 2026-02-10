#!/bin/bash
# Push dashboard redesign to ai-trading-ui repository for Railway auto-deployment
# This script adapts Next.js components to Create React App

set -e

AI_TRADING_UI_DIR="/Users/mikaelo/ai-trading-ui"
SOURCE_DIR="/Users/mikaelo/trading-bridge/frontend"

echo "=========================================="
echo "Dashboard Redesign Migration to Railway"
echo "=========================================="
echo ""

# Check directories
if [ ! -d "$AI_TRADING_UI_DIR" ]; then
    echo "❌ ai-trading-ui directory not found: $AI_TRADING_UI_DIR"
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Source directory not found: $SOURCE_DIR"
    exit 1
fi

cd "$AI_TRADING_UI_DIR"

echo "✅ Found ai-trading-ui repository"
echo "✅ Found source directory"
echo ""

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: Working directory has uncommitted changes"
    echo "   Committing them first..."
    git add .
    git commit -m "Pre-migration commit" || true
fi

echo "📦 Step 1: Installing required dependencies..."
npm install --save \
    @radix-ui/react-accordion \
    @radix-ui/react-slot \
    class-variance-authority \
    clsx \
    tailwind-merge \
    lucide-react

echo ""
echo "✅ Dependencies installed"
echo ""

echo "📁 Step 2: Creating directory structure..."
mkdir -p src/components/dashboard
mkdir -p src/components/ui
mkdir -p src/lib

echo "✅ Directories created"
echo ""

echo "📋 Step 3: Copying and adapting components..."

# Copy utils
cp "$SOURCE_DIR/lib/utils.ts" src/lib/utils.js
sed -i '' "s/import { clsx, type ClassValue }/import { clsx }/g" src/lib/utils.js
sed -i '' "s/export function cn(...inputs: ClassValue\[\])/export function cn(...inputs)/g" src/lib/utils.js

# Copy UI components (we'll adapt them)
echo "   Copying UI components..."
cp "$SOURCE_DIR/components/ui/button.tsx" src/components/ui/button.jsx
cp "$SOURCE_DIR/components/ui/badge.tsx" src/components/ui/badge.jsx
cp "$SOURCE_DIR/components/ui/card.tsx" src/components/ui/card.jsx
cp "$SOURCE_DIR/components/ui/accordion.tsx" src/components/ui/accordion.jsx

# Adapt UI components for CRA
echo "   Adapting UI components for Create React App..."
for file in src/components/ui/*.jsx; do
    # Remove TypeScript types
    sed -i '' 's/: [A-Za-z<>\[\]{}|&,() ]*//g' "$file"
    sed -i '' 's/type [A-Za-z]* = [^;]*;//g' "$file"
    sed -i '' 's/interface [A-Za-z]*[^}]*}//g' "$file"
    # Fix imports
    sed -i '' "s|@/lib/utils|../../lib/utils|g" "$file"
    sed -i '' "s/'use client'//g" "$file"
    sed -i '' 's/"use client"//g' "$file"
    # Fix React imports
    sed -i '' "s/import \* as React/import React/g" "$file"
done

# Copy dashboard components
echo "   Copying dashboard components..."
cp "$SOURCE_DIR/components/dashboard/welcome-header.tsx" src/components/dashboard/welcome-header.jsx
cp "$SOURCE_DIR/components/dashboard/stats-overview.tsx" src/components/dashboard/stats-overview.jsx
cp "$SOURCE_DIR/components/dashboard/bots-list.tsx" src/components/dashboard/bots-list.jsx
cp "$SOURCE_DIR/components/dashboard/bot-card.tsx" src/components/dashboard/bot-card.jsx

# Adapt dashboard components
echo "   Adapting dashboard components..."
for file in src/components/dashboard/*.jsx; do
    # Remove TypeScript
    sed -i '' 's/: [A-Za-z<>\[\]{}|&,() ]*//g' "$file"
    sed -i '' 's/type [A-Za-z]* = [^;]*;//g' "$file"
    sed -i '' 's/interface [A-Za-z]*[^}]*}//g' "$file"
    # Fix imports
    sed -i '' "s|@/components/ui|../ui|g" "$file"
    sed -i '' "s|@/lib/utils|../../lib/utils|g" "$file"
    sed -i '' "s|@/components/dashboard|.|g" "$file"
    sed -i '' "s/'use client'//g" "$file"
    sed -i '' 's/"use client"//g' "$file"
done

echo "✅ Components copied and adapted"
echo ""

echo "🎨 Step 4: Updating Tailwind config..."
# Update tailwind config to include CSS variables
cat >> tailwind.config.js << 'EOF'

// Add CSS variables support
theme: {
  extend: {
    colors: {
      border: "hsl(var(--border))",
      input: "hsl(var(--input))",
      ring: "hsl(var(--ring))",
      background: "hsl(var(--background))",
      foreground: "hsl(var(--foreground))",
      primary: {
        DEFAULT: "hsl(var(--primary))",
        foreground: "hsl(var(--primary-foreground))",
      },
      secondary: {
        DEFAULT: "hsl(var(--secondary))",
        foreground: "hsl(var(--secondary-foreground))",
      },
      muted: {
        DEFAULT: "hsl(var(--muted))",
        foreground: "hsl(var(--muted-foreground))",
      },
      card: {
        DEFAULT: "hsl(var(--card))",
        foreground: "hsl(var(--card-foreground))",
      },
    },
    borderRadius: {
      lg: "var(--radius)",
      md: "calc(var(--radius) - 2px)",
      sm: "calc(var(--radius) - 4px)",
    },
  },
},
EOF

echo "✅ Tailwind config updated"
echo ""

echo "📝 Step 5: Adding CSS variables to globals.css..."
cat >> src/styles/globals.css << 'EOF'

/* Dashboard redesign CSS variables */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}
EOF

echo "✅ CSS variables added"
echo ""

echo "📦 Step 6: Committing changes..."
git add .
git commit -m "Add dashboard redesign - Next.js components adapted for CRA" || echo "⚠️  No changes to commit"

echo ""
echo "=========================================="
echo "✅ Migration Complete!"
echo "=========================================="
echo ""
echo "Next: Push to trigger Railway auto-deployment"
echo "  git push origin main"
echo ""
