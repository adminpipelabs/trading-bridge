"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Bot, Settings, HelpCircle, Sparkles, Menu, X, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"

const navItems = [
  { label: "Dashboard", href: "#", icon: Bot, active: true },
  { label: "Settings", href: "#settings", icon: Settings, active: false },
  { label: "Help", href: "#help", icon: HelpCircle, active: false },
]

interface NavbarProps {
  onToggleAi: () => void
  aiOpen: boolean
}

export function Navbar({ onToggleAi, aiOpen }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-card">
      <div className="flex h-14 items-center justify-between px-4 lg:px-6">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary font-mono text-sm font-bold text-primary-foreground">
            P
          </div>
          <span className="text-base font-semibold tracking-tight text-foreground">
            Pipe Labs
          </span>
        </div>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-1 md:flex" aria-label="Main navigation">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className={cn(
                "relative flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                item.active
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
              {item.active && (
                <span className="absolute bottom-0 left-3 right-3 h-0.5 rounded-full bg-primary" />
              )}
            </a>
          ))}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {/* AI toggle - desktop only */}
          <Button
            variant={aiOpen ? "default" : "outline"}
            size="sm"
            onClick={onToggleAi}
            className={cn(
              "hidden gap-2 lg:flex",
              aiOpen
                ? "bg-primary text-primary-foreground hover:bg-primary/90"
                : "border-border bg-transparent text-muted-foreground hover:border-primary/30 hover:text-foreground"
            )}
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span className="text-xs">AI Assistant</span>
          </Button>

          <div className="hidden items-center gap-2 rounded-full border border-border bg-secondary/50 px-3 py-1.5 sm:flex">
            <span className="h-2 w-2 rounded-full bg-primary" />
            <span className="font-mono text-xs text-muted-foreground">
              0xb4...85a
            </span>
          </div>

          {/* Mobile menu button */}
          <Button
            variant="ghost"
            size="sm"
            className="md:hidden"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile Nav */}
      {mobileOpen && (
        <nav className="border-t border-border bg-card px-4 pb-4 pt-2 md:hidden" aria-label="Mobile navigation">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                item.active
                  ? "bg-primary/5 text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </a>
          ))}
          <div className="mt-3 flex items-center gap-2 rounded-lg border border-border bg-secondary/50 px-3 py-2">
            <span className="h-2 w-2 rounded-full bg-primary" />
            <span className="font-mono text-xs text-muted-foreground">0xb4...85a</span>
          </div>
        </nav>
      )}
    </header>
  )
}
