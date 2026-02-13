import { BarChart3, TrendingUp, Clock, MessageSquare, Users } from 'lucide-react';
import { useBots } from '../hooks/useBots';

function StatCard({ label, value, change, icon: Icon }: {
  label: string;
  value: string;
  change: string;
  icon: any;
}) {
  const isPositive = change.startsWith('+');
  return (
    <div className="bg-slate-800/40 border border-slate-700/40 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-slate-400">{label}</span>
        <Icon className="w-4 h-4 text-slate-500" />
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className={`text-xs mt-1 ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
        {change} from last week
      </p>
    </div>
  );
}

export default function Analytics() {
  const { selectedBot } = useBots();

  if (!selectedBot) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        Select a bot from the dashboard first
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-8 py-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-sm text-slate-400 mt-1">
          Performance metrics for <span className="text-white font-medium">{selectedBot.name}</span>
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Messages" value="1,234" change="+12%" icon={MessageSquare} />
        <StatCard label="Avg Response" value="1.2s" change="-0.3s" icon={Clock} />
        <StatCard label="Users" value="89" change="+5" icon={Users} />
        <StatCard label="Satisfaction" value="94%" change="+2%" icon={TrendingUp} />
      </div>

      {/* Placeholder chart area */}
      <div className="bg-slate-800/40 border border-slate-700/40 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-indigo-400" />
          <h2 className="text-white font-semibold">Message Volume</h2>
        </div>
        <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
          Chart data will appear once {selectedBot.name} starts handling messages
        </div>
      </div>
    </div>
  );
}
