import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Puzzle, BarChart3, Rocket, Bot, ChevronUp } from 'lucide-react';
import { useBots } from '../../hooks/useBots';
import { useState } from 'react';

export function MobileNav() {
  const { bots, selectedBot, selectBot, isAuthenticated } = useBots();
  const [showBotMenu, setShowBotMenu] = useState(false);
  const hasDrafts = bots.some(b => b.status === 'draft');

  const navItems = [
    { to: '/dashboard', label: 'Home', icon: LayoutDashboard },
    { to: '/chat', label: 'Chat', icon: MessageSquare },
    { to: '/integrations', label: 'Integrate', icon: Puzzle },
    { to: '/analytics', label: 'Stats', icon: BarChart3 },
    // Show Activate instead of generic settings if sandbox mode
    ...(!isAuthenticated && hasDrafts
      ? [{ to: '/activate', label: 'Activate', icon: Rocket }]
      : [{ to: '/settings', label: 'Settings', icon: BarChart3 }]),
  ];

  return (
    <div className="lg:hidden">
      {/* Bot picker popup */}
      {showBotMenu && (
        <div className="fixed inset-0 z-40" onClick={() => setShowBotMenu(false)}>
          <div className="absolute bottom-20 left-4 right-4 bg-slate-800 border border-slate-600 rounded-2xl shadow-2xl p-2 max-h-60 overflow-y-auto">
            <p className="px-3 py-1 text-xs text-slate-500 font-medium">Switch Bot</p>
            {bots.map((bot) => (
              <button
                key={bot.id}
                onClick={(e) => { e.stopPropagation(); selectBot(bot.id); setShowBotMenu(false); }}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                  selectedBot?.id === bot.id ? 'bg-indigo-600/15' : 'hover:bg-slate-700/50'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${
                  bot.status === 'online' ? 'bg-emerald-400' :
                  bot.status === 'draft' ? 'bg-amber-400' :
                  'bg-slate-500'
                }`} />
                <span className="text-sm text-white truncate">{bot.name}</span>
                {bot.status === 'draft' && (
                  <span className="text-[10px] text-amber-400 ml-auto">Draft</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-slate-800/95 backdrop-blur-xl border-t border-slate-700/50 px-2 pb-[env(safe-area-inset-bottom)] z-30">
        {/* Bot name bar */}
        {bots.length > 0 && (
          <button
            onClick={() => setShowBotMenu(!showBotMenu)}
            className="w-full flex items-center justify-center gap-2 py-1.5 text-xs text-slate-400 border-b border-slate-700/30"
          >
            <Bot className={`w-3 h-3 ${selectedBot?.status === 'draft' ? 'text-amber-400' : 'text-indigo-400'}`} />
            <span className="truncate max-w-[150px]">{selectedBot?.name || 'No bot'}</span>
            {selectedBot?.status === 'draft' && (
              <span className="text-[10px] text-amber-400 px-1.5 py-0 bg-amber-500/10 rounded">Draft</span>
            )}
            <ChevronUp className={`w-3 h-3 transition-transform ${showBotMenu ? 'rotate-180' : ''}`} />
          </button>
        )}

        <div className="flex items-center justify-around py-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 px-2 py-1 transition-colors ${
                  isActive ? 'text-indigo-400' : 'text-slate-500'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
