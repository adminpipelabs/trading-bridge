"use client"

import { Plus, BarChart3, ArrowUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { BotCard, type BotData } from "./bot-card"

const bots: BotData[] = [
  {
    name: "Sharp-SB-BitMart",
    type: "spread",
    status: "running",
    availableSharp: "12,450",
    availableUsdt: "3,200",
    lockedSharp: "5,000",
    lockedUsdt: "1,800",
    metric: "Buy/Sell",
    metricValue: "142 buys, 89 sells",
    pnl: "+$482.30",
    pnlPositive: true,
    recentActivity: [
      { time: "2m ago", action: "Buy order filled", amount: "+50 SHARP" },
      { time: "5m ago", action: "Sell order placed", amount: "-25 SHARP" },
      { time: "12m ago", action: "Spread adjusted", amount: "0.15%" },
    ],
  },
  {
    name: "SHARP Volume Bot - Coinstore",
    type: "volume",
    status: "stopped",
    availableSharp: "8,200",
    availableUsdt: "2,100",
    lockedSharp: "0",
    lockedUsdt: "0",
    metric: "Volume",
    metricValue: "$12,450",
    pnl: "+$165.80",
    pnlPositive: true,
    recentActivity: [],
  },
  {
    name: "SHARP Spread Bot",
    type: "spread",
    status: "running",
    availableSharp: "15,800",
    availableUsdt: "4,500",
    lockedSharp: "8,200",
    lockedUsdt: "2,300",
    metric: "Buy/Sell",
    metricValue: "267 buys, 198 sells",
    pnl: "+$312.45",
    pnlPositive: true,
    recentActivity: [
      { time: "1m ago", action: "Sell order filled", amount: "-100 SHARP" },
      { time: "3m ago", action: "Buy order filled", amount: "+75 SHARP" },
    ],
  },
  {
    name: "SHARP-MEXC Volume",
    type: "volume",
    status: "running",
    availableSharp: "6,300",
    availableUsdt: "1,950",
    lockedSharp: "3,100",
    lockedUsdt: "900",
    metric: "Volume",
    metricValue: "$8,920",
    pnl: "+$89.50",
    pnlPositive: true,
    recentActivity: [
      { time: "8m ago", action: "Volume cycle completed", amount: "$2,400" },
    ],
  },
  {
    name: "BTC Spread - Binance",
    type: "spread",
    status: "running",
    availableSharp: "0",
    availableUsdt: "12,400",
    lockedSharp: "0",
    lockedUsdt: "5,600",
    metric: "Buy/Sell",
    metricValue: "523 buys, 491 sells",
    pnl: "+$197.77",
    pnlPositive: true,
    recentActivity: [
      { time: "30s ago", action: "Buy order filled", amount: "+0.002 BTC" },
      { time: "1m ago", action: "Sell order filled", amount: "-0.003 BTC" },
      { time: "4m ago", action: "Spread tightened", amount: "0.08%" },
    ],
  },
  {
    name: "SHARP-Gate Volume",
    type: "volume",
    status: "stopped",
    availableSharp: "4,100",
    availableUsdt: "980",
    lockedSharp: "0",
    lockedUsdt: "0",
    metric: "Volume",
    metricValue: "$0",
    pnl: "-$12.40",
    pnlPositive: false,
    recentActivity: [],
  },
]

const botTypeCounts = {
  spread: bots.filter((b) => b.type === "spread").length,
  volume: bots.filter((b) => b.type === "volume").length,
  running: bots.filter((b) => b.status === "running").length,
}

export function BotsList() {
  return (
    <section>
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
          <h2 className="text-lg font-semibold text-foreground sm:text-xl">
            Your Bots
            <span className="ml-2 font-mono text-sm text-muted-foreground">({bots.length})</span>
          </h2>
          <div className="flex items-center gap-1.5">
            <Badge variant="outline" className="gap-1 border-primary/20 bg-primary/5 text-xs text-primary">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              {botTypeCounts.running} active
            </Badge>
            <Badge variant="outline" className="border-border text-xs text-muted-foreground">
              {botTypeCounts.spread} spread
            </Badge>
            <Badge variant="outline" className="border-border text-xs text-muted-foreground">
              {botTypeCounts.volume} volume
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-2 border-border bg-transparent text-muted-foreground hover:text-foreground"
          >
            <ArrowUpDown className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sort</span>
          </Button>
          <Button size="sm" className="gap-2 bg-primary text-primary-foreground shadow-sm hover:bg-primary/90">
            <Plus className="h-3.5 w-3.5" />
            <BarChart3 className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Volume Bot</span>
            <span className="sm:hidden">Volume</span>
          </Button>
          <Button size="sm" className="gap-2 bg-primary text-primary-foreground shadow-sm hover:bg-primary/90">
            <Plus className="h-3.5 w-3.5" />
            <ArrowUpDown className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Spread Bot</span>
            <span className="sm:hidden">Spread</span>
          </Button>
        </div>
      </div>

      {/* Bot Cards */}
      <div className="mt-5 space-y-3">
        {bots.map((bot) => (
          <BotCard key={bot.name} bot={bot} />
        ))}
      </div>
    </section>
  )
}
