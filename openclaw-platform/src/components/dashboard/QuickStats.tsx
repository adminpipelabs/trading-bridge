import { MessageSquare, Clock, Wifi, TrendingUp } from 'lucide-react';

interface StatItem {
  label: string;
  value: string;
  change?: string;
  changePositive?: boolean;
  icon: React.ComponentType<{ className?: string }>;
}

const stats: StatItem[] = [
  {
    label: 'Messages Today',
    value: '47',
    change: '+12%',
    changePositive: true,
    icon: MessageSquare,
  },
  {
    label: 'Avg Response',
    value: '1.2s',
    change: '-0.3s',
    changePositive: true,
    icon: Clock,
  },
  {
    label: 'Active Channels',
    value: '3',
    icon: Wifi,
  },
  {
    label: 'This Week',
    value: '312',
    change: '+23%',
    changePositive: true,
    icon: TrendingUp,
  },
];

export function QuickStats() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-4"
        >
          <div className="flex items-center justify-between mb-2">
            <stat.icon className="w-4 h-4 text-slate-500" />
            {stat.change && (
              <span
                className={`text-xs font-medium ${
                  stat.changePositive ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {stat.change}
              </span>
            )}
          </div>
          <p className="text-xl font-bold text-white">{stat.value}</p>
          <p className="text-xs text-slate-500 mt-0.5">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}
