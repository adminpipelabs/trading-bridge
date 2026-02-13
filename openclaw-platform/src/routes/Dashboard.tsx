import { Link } from 'react-router-dom';
import { Plus, MessageSquare, Power, Settings, Trash2, MoreVertical, Zap, Rocket } from 'lucide-react';
import { useBots, type BotData } from '../hooks/useBots';
import { QuickStats } from '../components/dashboard/QuickStats';
import { OpportunityCards } from '../components/dashboard/OpportunityCards';
import { useState } from 'react';

function BotCard({ bot, isSelected, onSelect, onDelete }: {
  bot: BotData;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const isDraft = bot.status === 'draft';

  const statusColors: Record<string, string> = {
    online: 'bg-emerald-400',
    offline: 'bg-slate-500',
    starting: 'bg-amber-400 animate-pulse',
    draft: 'bg-amber-400',
  };

  const statusLabels: Record<string, string> = {
    online: 'Online — 24/7',
    offline: 'Offline',
    starting: 'Starting...',
    draft: 'Draft — not active',
  };

  return (
    <div
      onClick={onSelect}
      className={`relative bg-slate-800/40 border rounded-2xl p-5 cursor-pointer transition-all hover:border-slate-500/60 ${
        isSelected ? 'border-indigo-500/50 ring-1 ring-indigo-500/20' : 'border-slate-700/40'
      } ${isDraft ? 'border-dashed' : ''}`}
    >
      {/* Status + menu */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${statusColors[bot.status] || statusColors.offline}`} />
          <span className={`text-xs capitalize ${isDraft ? 'text-amber-400' : 'text-slate-400'}`}>
            {statusLabels[bot.status] || bot.status}
          </span>
        </div>
        <div className="relative">
          <button
            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
            className="p-1 text-slate-500 hover:text-white transition-colors rounded"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
          {showMenu && (
            <div className="absolute right-0 top-8 bg-slate-700 border border-slate-600 rounded-lg shadow-xl z-10 py-1 min-w-[140px]">
              <Link
                to="/settings"
                onClick={(e) => { e.stopPropagation(); onSelect(); }}
                className="flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-600/50 transition-colors"
              >
                <Settings className="w-3.5 h-3.5" />
                Settings
              </Link>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(); setShowMenu(false); }}
                className="flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-slate-600/50 transition-colors w-full text-left"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Delete
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Bot info */}
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
          isDraft ? 'bg-amber-600/15' : 'bg-indigo-600/20'
        }`}>
          <Power className={`w-5 h-5 ${isDraft ? 'text-amber-400' : 'text-indigo-400'}`} />
        </div>
        <div>
          <h3 className="text-white font-semibold text-sm">{bot.name}</h3>
          <p className="text-xs text-slate-500 capitalize">{bot.persona} &middot; {bot.model}</p>
        </div>
      </div>

      {/* Channel */}
      {bot.channel && (
        <div className="flex items-center gap-1.5 mb-3">
          <span className="text-[10px] bg-slate-700/50 text-slate-300 px-2 py-0.5 rounded-md capitalize">
            {bot.channel}
          </span>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 mt-2">
        {isDraft ? (
          <Link
            to="/activate"
            onClick={(e) => { e.stopPropagation(); onSelect(); }}
            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 transition-colors"
          >
            <Rocket className="w-3.5 h-3.5" />
            Activate Bot
          </Link>
        ) : (
          <>
            <Link
              to="/chat"
              onClick={(e) => { e.stopPropagation(); onSelect(); }}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium bg-indigo-600/15 text-indigo-300 rounded-lg hover:bg-indigo-600/25 transition-colors"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              Chat
            </Link>
            <Link
              to="/settings"
              onClick={(e) => { e.stopPropagation(); onSelect(); }}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium bg-slate-700/40 text-slate-300 rounded-lg hover:bg-slate-700/60 transition-colors"
            >
              <Settings className="w-3.5 h-3.5" />
              Configure
            </Link>
          </>
        )}
      </div>

      {/* Selected indicator */}
      {isSelected && !isDraft && (
        <div className="absolute -top-px -right-px px-2 py-0.5 bg-indigo-600 text-white text-[10px] font-medium rounded-bl-lg rounded-tr-2xl">
          Active
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const { bots, selectedBot, selectBot, deleteBot, isAuthenticated } = useBots();
  const hasDrafts = bots.some(b => b.status === 'draft');

  return (
    <div className="px-4 sm:px-8 py-6 max-w-5xl mx-auto">
      {/* Sandbox banner */}
      {!isAuthenticated && hasDrafts && (
        <div className="mb-6 bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start gap-3">
          <Zap className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-amber-200 font-medium">Sandbox Mode</p>
            <p className="text-xs text-slate-400 mt-0.5">
              Your bots are saved locally. Activate them to run 24/7 on cloud infrastructure with monitoring.
            </p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            {bots.length} bot{bots.length !== 1 ? 's' : ''} — manage them all from here
          </p>
        </div>
        <Link
          to="/onboarding"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Bot
        </Link>
      </div>

      <div className="space-y-6">
        {/* Bot grid */}
        {bots.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {bots.map((bot) => (
              <BotCard
                key={bot.id}
                bot={bot}
                isSelected={selectedBot?.id === bot.id}
                onSelect={() => selectBot(bot.id)}
                onDelete={() => {
                  if (confirm(`Delete "${bot.name}"? This cannot be undone.`)) {
                    deleteBot(bot.id);
                  }
                }}
              />
            ))}

            {/* New bot card */}
            <Link
              to="/onboarding"
              className="flex flex-col items-center justify-center bg-slate-800/20 border border-dashed border-slate-700/40 rounded-2xl p-8 hover:border-indigo-500/40 hover:bg-slate-800/30 transition-all min-h-[200px]"
            >
              <div className="w-12 h-12 rounded-xl bg-slate-700/30 flex items-center justify-center mb-3">
                <Plus className="w-6 h-6 text-slate-500" />
              </div>
              <span className="text-sm text-slate-500 font-medium">Create Another Bot</span>
            </Link>
          </div>
        ) : (
          <div className="text-center py-16">
            <Power className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-white mb-2">No bots yet</h2>
            <p className="text-slate-400 mb-6">Create your first bot to get started.</p>
            <Link
              to="/onboarding"
              className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Your First Bot
            </Link>
          </div>
        )}

        {/* Stats for selected bot (only for active/claimed bots) */}
        {selectedBot && selectedBot.status !== 'draft' && (
          <>
            <div>
              <h2 className="text-sm font-medium text-slate-400 mb-3">
                Stats for {selectedBot.name}
              </h2>
              <QuickStats />
            </div>
            <OpportunityCards />
          </>
        )}
      </div>
    </div>
  );
}
