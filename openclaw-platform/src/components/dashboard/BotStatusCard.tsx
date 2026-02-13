import { Activity, Power } from 'lucide-react';

interface Props {
  name: string;
  status: 'online' | 'offline' | 'starting';
  uptime: number; // hours
  lastActive: string;
}

export function BotStatusCard({ name, status, uptime, lastActive }: Props) {
  const statusColors = {
    online: 'bg-emerald-400',
    offline: 'bg-red-400',
    starting: 'bg-amber-400 animate-pulse',
  };

  const statusLabels = {
    online: 'Online',
    offline: 'Offline',
    starting: 'Starting...',
  };

  return (
    <div className="bg-slate-800/40 border border-slate-700/40 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 flex items-center justify-center">
            <Power className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-white font-semibold">{name}</h3>
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${statusColors[status]}`} />
              <span className="text-xs text-slate-400">{statusLabels[status]}</span>
            </div>
          </div>
        </div>
        <Activity className="w-5 h-5 text-slate-600" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-slate-500">Uptime</p>
          <p className="text-sm text-white font-medium">{uptime}h</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Last Active</p>
          <p className="text-sm text-white font-medium">{lastActive}</p>
        </div>
      </div>
    </div>
  );
}
