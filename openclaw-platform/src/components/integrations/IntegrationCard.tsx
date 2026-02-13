import { Check, Plus, Clock } from 'lucide-react';
import type { Integration } from '../../types';

interface Props {
  integration: Integration;
  onConnect: (id: string) => void;
}

export function IntegrationCard({ integration, onConnect }: Props) {
  const { id, name, description, status, popular } = integration;

  return (
    <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-5 flex flex-col">
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-xl bg-slate-700/50 flex items-center justify-center text-lg">
          {integration.icon}
        </div>
        {popular && (
          <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full font-medium">
            Popular
          </span>
        )}
      </div>

      <h3 className="text-white font-medium text-sm">{name}</h3>
      <p className="text-xs text-slate-400 mt-1 leading-relaxed flex-1">{description}</p>

      <div className="mt-4">
        {status === 'connected' && (
          <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
            <Check className="w-3.5 h-3.5" />
            Connected
          </div>
        )}
        {status === 'available' && (
          <button
            onClick={() => onConnect(id)}
            className="flex items-center gap-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Connect
          </button>
        )}
        {status === 'coming_soon' && (
          <div className="flex items-center gap-1.5 text-slate-500 text-xs">
            <Clock className="w-3.5 h-3.5" />
            Coming Soon
          </div>
        )}
      </div>
    </div>
  );
}
