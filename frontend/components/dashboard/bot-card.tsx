"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import {
  Play,
  Square,
  Pencil,
  Trash2,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  TrendingUp,
  Clock,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export interface BotData {
  name: string
  type: "spread" | "volume"
  status: "running" | "stopped"
  availableSharp: string
  availableUsdt: string
  lockedSharp: string
  lockedUsdt: string
  metric: string
  metricValue: string
  pnl: string
  pnlPositive: boolean
  recentActivity: { time: string; action: string; amount: string }[]
}

export function BotCard({ bot }: { bot: BotData }) {
  const [expanded, setExpanded] = useState(false)
  const isRunning = bot.status === "running"

  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-xl border bg-card shadow-sm transition-all duration-200",
        isRunning
          ? "border-primary/15 hover:border-primary/30 hover:shadow-md hover:shadow-primary/5"
          : "border-border hover:border-border hover:shadow-md hover:shadow-muted/10"
      )}
    >
      {/* Status indicator line */}
      <div
        className={cn(
          "absolute left-0 top-0 h-full w-[3px]",
          isRunning ? "bg-primary" : "bg-muted-foreground/20"
        )}
      />

      <div className="p-4 pl-5 sm:p-5 sm:pl-6">
        {/* Header row */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground sm:text-base">{bot.name}</h3>
            <Badge
              className={cn(
                "gap-1.5 border-0 text-xs font-medium",
                isRunning
                  ? "bg-primary/10 text-primary"
                  : "bg-muted text-muted-foreground"
              )}
            >
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  isRunning ? "bg-primary animate-pulse" : "bg-muted-foreground/50"
                )}
              />
              {isRunning ? "Running" : "Stopped"}
            </Badge>
            <Badge variant="outline" className="border-border text-xs text-muted-foreground">
              {bot.type === "spread" ? "Spread" : "Volume"}
            </Badge>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1.5">
            {isRunning ? (
              <Button
                variant="outline"
                size="sm"
                className="h-8 w-8 border-destructive/20 bg-transparent p-0 text-destructive/70 hover:border-destructive/40 hover:bg-destructive/5 hover:text-destructive"
                aria-label="Stop bot"
              >
                <Square className="h-3.5 w-3.5" />
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                className="h-8 w-8 border-primary/20 bg-transparent p-0 text-primary/70 hover:border-primary/40 hover:bg-primary/5 hover:text-primary"
                aria-label="Start bot"
              >
                <Play className="h-3.5 w-3.5" />
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              className="h-8 w-8 border-border bg-transparent p-0 text-muted-foreground hover:border-warning/40 hover:bg-warning/5 hover:text-warning"
              aria-label="Edit bot"
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-8 w-8 border-border bg-transparent p-0 text-muted-foreground hover:border-destructive/40 hover:bg-destructive/5 hover:text-destructive"
              aria-label="Delete bot"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Metrics grid */}
        <div className="mt-4 grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="min-w-0">
            <span className="text-xs text-muted-foreground">Available</span>
            <p className="truncate font-mono text-xs text-foreground sm:text-sm">
              {bot.availableSharp} SHARP | {bot.availableUsdt} USDT
            </p>
          </div>
          <div className="min-w-0">
            <span className="text-xs text-muted-foreground">Locked</span>
            <p className="truncate font-mono text-xs text-foreground sm:text-sm">
              {bot.lockedSharp} SHARP | {bot.lockedUsdt} USDT
            </p>
          </div>
          <div className="min-w-0">
            <span className="text-xs text-muted-foreground">{bot.metric}</span>
            <p className="truncate font-mono text-xs text-foreground sm:text-sm">{bot.metricValue}</p>
          </div>
          <div className="flex items-end justify-between gap-2 sm:items-center">
            <div>
              <span className="text-xs text-muted-foreground">{"P&L"}</span>
              <p
                className={cn(
                  "font-mono text-xs font-semibold sm:text-sm",
                  bot.pnlPositive ? "text-primary" : "text-destructive"
                )}
              >
                {bot.pnl}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-1.5 border-border bg-transparent text-xs text-primary hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
            >
              <RefreshCw className="h-3 w-3" />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
          </div>
        </div>

        {/* Recent Activity Toggle */}
        <button
          type="button"
          className="mt-4 flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
          Recent Activity
        </button>

        {/* Expanded Activity */}
        {expanded && (
          <div className="mt-3 space-y-2 border-t border-border pt-3">
            {bot.recentActivity.length > 0 ? (
              bot.recentActivity.map((activity, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 rounded-lg bg-muted/50 px-3 py-2"
                >
                  <Clock className="h-3.5 w-3.5 flex-shrink-0 text-muted-foreground" />
                  <span className="font-mono text-xs text-muted-foreground">
                    {activity.time}
                  </span>
                  <span className="text-xs text-foreground">{activity.action}</span>
                  <span className="ml-auto font-mono text-xs text-primary">
                    {activity.amount}
                  </span>
                </div>
              ))
            ) : (
              <div className="flex items-center gap-2 py-2 text-xs text-muted-foreground">
                <TrendingUp className="h-3.5 w-3.5" />
                No recent activity
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
