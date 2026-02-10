# Railway Frontend Migration Guide

**Target:** `ai-trading-ui` repository on Railway  
**Source:** `trading-bridge/frontend/` (dashboard redesign)  
**Status:** Ready to migrate

---

## 🎯 **What We're Doing**

Copying the new dashboard redesign from `trading-bridge/frontend/` to the `ai-trading-ui` Railway repository.

**The redesign includes:**
- ✅ Complete Next.js 16 dashboard
- ✅ WelcomeHeader, StatsOverview, BotsList, BotCard components
- ✅ Full shadcn/ui component library
- ✅ TypeScript + Tailwind CSS

---

## 📋 **Step-by-Step Migration**

### **Step 1: Clone ai-trading-ui Repository**

```bash
# Clone the Railway frontend repo
git clone https://github.com/[your-org]/ai-trading-ui.git
cd ai-trading-ui
```

---

### **Step 2: Check Current Stack**

**Check what framework is currently used:**
```bash
cat package.json
```

**If it's already Next.js:**
- ✅ Perfect! Can copy components directly
- Skip to Step 3

**If it's React (Create React App/Vite):**
- ⚠️ Need to adapt components (see Step 2b)

---

### **Step 3: Copy Dashboard Components**

**From `trading-bridge/frontend/` to `ai-trading-ui/`:**

```bash
# Copy dashboard components
cp -r /path/to/trading-bridge/frontend/components/dashboard ai-trading-ui/src/components/

# Copy UI components (if not already present)
cp -r /path/to/trading-bridge/frontend/components/ui ai-trading-ui/src/components/

# Copy hooks (if needed)
cp -r /path/to/trading-bridge/frontend/hooks ai-trading-ui/src/

# Copy lib utilities
cp /path/to/trading-bridge/frontend/lib/utils.ts ai-trading-ui/src/lib/
```

---

### **Step 4: Install Dependencies**

**Add missing packages to `package.json`:**

```bash
cd ai-trading-ui
npm install --save \
  @radix-ui/react-accordion \
  @radix-ui/react-alert-dialog \
  @radix-ui/react-avatar \
  @radix-ui/react-checkbox \
  @radix-ui/react-dialog \
  @radix-ui/react-dropdown-menu \
  @radix-ui/react-label \
  @radix-ui/react-popover \
  @radix-ui/react-select \
  @radix-ui/react-separator \
  @radix-ui/react-slot \
  @radix-ui/react-switch \
  @radix-ui/react-tabs \
  @radix-ui/react-toast \
  @radix-ui/react-tooltip \
  class-variance-authority \
  clsx \
  tailwind-merge \
  lucide-react \
  next-themes \
  date-fns \
  recharts \
  sonner \
  vaul \
  zod \
  react-hook-form \
  @hookform/resolvers
```

**Or if using pnpm:**
```bash
pnpm add [same packages as above]
```

---

### **Step 5: Update Tailwind Config**

**Check if `tailwind.config.js` exists, then merge:**

```javascript
// tailwind.config.js
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
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
        // ... (see frontend/tailwind.config.ts for full config)
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

---

### **Step 6: Update Global CSS**

**Add to `src/index.css` or `src/App.css`:**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
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
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}
```

---

### **Step 7: Connect API Endpoints**

**Update `components/dashboard/stats-overview.tsx`:**

```typescript
// Replace mock data with real API call
import useSWR from 'swr'
import { tradingBridge } from '@/services/api'

export function StatsOverview() {
  const { data: stats, error } = useSWR(
    '/clients/current/stats',
    () => tradingBridge.getClientStats()
  )

  if (error) return <div>Error loading stats</div>
  if (!stats) return <div>Loading...</div>

  return (
    // ... use stats data
  )
}
```

**Update `components/dashboard/bots-list.tsx`:**

```typescript
import useSWR from 'swr'
import { tradingBridge } from '@/services/api'

export function BotsList() {
  const { data: bots, error, mutate } = useSWR(
    '/clients/current/bots',
    () => tradingBridge.getBots()
  )

  // Auto-refresh every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => mutate(), 5000)
    return () => clearInterval(interval)
  }, [mutate])

  // ... render bots
}
```

---

### **Step 8: Add Theme Provider**

**Wrap app with ThemeProvider (if using Next.js):**

```typescript
// app/layout.tsx or _app.tsx
import { ThemeProvider } from '@/components/theme-provider'

export default function RootLayout({ children }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system">
      {children}
    </ThemeProvider>
  )
}
```

**Or for React (non-Next.js):**

```typescript
// src/App.tsx
import { ThemeProvider } from '@/components/theme-provider'

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system">
      {/* Your app */}
    </ThemeProvider>
  )
}
```

---

### **Step 9: Create Dashboard Page**

**Create or update the main dashboard page:**

```typescript
// src/pages/Dashboard.tsx or src/app/page.tsx
import { WelcomeHeader } from '@/components/dashboard/welcome-header'
import { StatsOverview } from '@/components/dashboard/stats-overview'
import { BotsList } from '@/components/dashboard/bots-list'
import { Navbar } from '@/components/dashboard/navbar'

export default function Dashboard() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1 p-6">
        <WelcomeHeader />
        <StatsOverview />
        <BotsList />
      </main>
    </div>
  )
}
```

---

### **Step 10: Connect Bot Actions**

**Update `components/dashboard/bot-card.tsx`:**

```typescript
import { tradingBridge } from '@/services/api'

export function BotCard({ bot }) {
  const handleStart = async () => {
    try {
      await tradingBridge.startBot(bot.id)
      // Refresh list
      mutate()
    } catch (error) {
      toast.error('Failed to start bot')
    }
  }

  const handleStop = async () => {
    try {
      await tradingBridge.stopBot(bot.id)
      mutate()
    } catch (error) {
      toast.error('Failed to stop bot')
    }
  }

  // ... render card with actions
}
```

---

### **Step 11: Test Locally**

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Test dashboard
# Open http://localhost:3000
```

---

### **Step 12: Commit and Push**

```bash
git add .
git commit -m "Add dashboard redesign - Next.js components"
git push origin main
```

**Railway will auto-deploy!** 🚀

---

## ✅ **Checklist**

- [ ] Cloned `ai-trading-ui` repo
- [ ] Copied dashboard components
- [ ] Copied UI components
- [ ] Installed dependencies
- [ ] Updated Tailwind config
- [ ] Updated global CSS
- [ ] Connected API endpoints
- [ ] Added ThemeProvider
- [ ] Created dashboard page
- [ ] Connected bot actions
- [ ] Tested locally
- [ ] Committed and pushed
- [ ] Verified Railway deployment

---

## 🐛 **Troubleshooting**

### **TypeScript Errors:**
- Make sure `tsconfig.json` includes `"paths"` for `@/*` alias
- Check that all dependencies are installed

### **Component Not Found:**
- Verify import paths match file structure
- Check if components are in correct directories

### **Styling Issues:**
- Ensure Tailwind is configured correctly
- Check that CSS variables are defined
- Verify `tailwindcss-animate` plugin is installed

### **API Errors:**
- Check API base URL in `services/api.js`
- Verify CORS settings on backend
- Check authentication tokens

---

## 📚 **Reference Files**

**Source (trading-bridge/frontend/):**
- `components/dashboard/*` - Dashboard components
- `components/ui/*` - UI component library
- `tailwind.config.ts` - Tailwind configuration
- `app/globals.css` - Global styles

**Target (ai-trading-ui/):**
- `src/components/dashboard/*` - Copy here
- `src/components/ui/*` - Copy here
- `tailwind.config.js` - Update this
- `src/index.css` - Update this

---

**Ready to migrate! Follow the steps above and Railway will auto-deploy.** 🚀
