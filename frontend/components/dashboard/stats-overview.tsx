import { Bot, TrendingUp, Wallet, Activity } from "lucide-react"

const stats = [
  {
    label: "Active Bots",
    value: "4",
    subtext: "of 6 total",
    icon: Bot,
    trend: "+2 this week",
    trendUp: true,
  },
  {
    label: "Total P&L",
    value: "+$1,247.82",
    subtext: "All time",
    icon: TrendingUp,
    trend: "+12.4%",
    trendUp: true,
  },
  {
    label: "Total Balance",
    value: "$8,432.50",
    subtext: "SHARP + USDT",
    icon: Wallet,
    trend: "Across 3 exchanges",
    trendUp: true,
  },
  {
    label: "24h Volume",
    value: "$24,891",
    subtext: "Combined",
    icon: Activity,
    trend: "+8.2% vs yesterday",
    trendUp: true,
  },
]

export function StatsOverview() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-xl border border-border bg-card p-4 shadow-sm transition-all hover:shadow-md hover:shadow-muted/10 sm:p-5"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground sm:text-sm">{stat.label}</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/8">
              <stat.icon className="h-4 w-4 text-primary" />
            </div>
          </div>
          <div className="mt-2 font-mono text-xl font-bold tracking-tight text-foreground sm:text-2xl">
            {stat.value}
          </div>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-xs text-muted-foreground">{stat.subtext}</span>
            <span className="text-xs font-medium text-primary">{stat.trend}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
