import { Copy } from "lucide-react"

export function WelcomeHeader() {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl text-balance">
          Welcome back, New Sharp Foundation
        </h1>
        <div className="mt-1.5 flex items-center gap-2">
          <span className="truncate font-mono text-xs text-muted-foreground">
            client_new_sharp_foundation
          </span>
          <button
            type="button"
            className="flex-shrink-0 text-muted-foreground transition-colors hover:text-primary"
            aria-label="Copy client ID"
          >
            <Copy className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
      <div className="flex items-center gap-2.5 self-start rounded-lg border border-border bg-card px-3 py-2 shadow-sm sm:self-auto">
        <span className="h-2 w-2 flex-shrink-0 rounded-full bg-primary" />
        <span className="text-xs text-muted-foreground">All Systems Operational</span>
      </div>
    </div>
  )
}
