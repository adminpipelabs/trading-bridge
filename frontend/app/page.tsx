"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/navbar"
import { WelcomeHeader } from "@/components/dashboard/welcome-header"
import { StatsOverview } from "@/components/dashboard/stats-overview"
import { BotsList } from "@/components/dashboard/bots-list"
import { AiChatPanel } from "@/components/dashboard/ai-chat-panel"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { MessageSquare } from "lucide-react"

export default function Page() {
  const [aiOpen, setAiOpen] = useState(false)

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar onToggleAi={() => setAiOpen(!aiOpen)} aiOpen={aiOpen} />

      <div className="flex flex-1 overflow-hidden">
        {/* Main dashboard content */}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
            <div className="space-y-6 sm:space-y-8">
              <WelcomeHeader />
              <StatsOverview />
              <BotsList />
            </div>
          </div>
        </main>

        {/* AI Panel - Desktop (right sidebar) */}
        <aside
          className={`hidden border-l border-border bg-card transition-all duration-300 lg:block ${
            aiOpen ? "w-[420px]" : "w-0 overflow-hidden border-l-0"
          }`}
        >
          {aiOpen && <AiChatPanel onClose={() => setAiOpen(false)} />}
        </aside>
      </div>

      {/* AI Panel - Mobile (bottom sheet) */}
      <div className="lg:hidden">
        <Sheet open={aiOpen} onOpenChange={setAiOpen}>
          <SheetTrigger asChild>
            <Button
              size="lg"
              className="fixed bottom-5 right-5 z-40 h-14 w-14 rounded-full bg-primary p-0 text-primary-foreground shadow-lg shadow-primary/20 hover:bg-primary/90"
              aria-label="Open AI Assistant"
            >
              <MessageSquare className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="bottom" className="h-[85vh] rounded-t-2xl border-t border-border bg-card p-0 [&>button:last-child]:hidden">
            <AiChatPanel onClose={() => setAiOpen(false)} />
          </SheetContent>
        </Sheet>
      </div>
    </div>
  )
}
