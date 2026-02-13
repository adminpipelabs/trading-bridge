import { NavLink, Link } from 'react-router-dom';
import { useState } from 'react';
import {
  LayoutDashboard,
  MessageSquare,
  Puzzle,
  BarChart3,
  Settings,
  LogOut,
  ChevronDown,
  Bot,
  Rocket,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useBots } from '../../hooks/useBots';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
  { to: '/integrations', label: 'Integrations', icon: Puzzle },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const { auth, logout } = useAuth();
  const { bots, selectedBot, selectBot, isAuthenticated } = useBots();
  const [showBotMenu, setShowBotMenu] = useState(false);

  return (
    <aside className="hidden lg:flex flex-col w-64 bg-slate-800/50 border-r border-slate-700/50 h-full">
      {/* Logo */}
      <div className="flex items-center gap-2 px-6 py-5 border-b border-slate-700/50">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
          B
        </div>
        <span className="text-white font-semibold text-lg">BotForge</span>
      </div>

      {/* Bot switcher */}
      {bots.length > 0 && (
        <div className="px-3 py-3 border-b border-slate-700/50 relative">
          <button
            onClick={() => setShowBotMenu(!showBotMenu)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-700/30 hover:bg-slate-700/50 transition-colors"
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
              selectedBot?.status === 'draft' ? 'bg-amber-600/15' : 'bg-indigo-600/20'
            }`}>
              <Bot className={`w-4 h-4 ${
                selectedBot?.status === 'draft' ? 'text-amber-400' : 'text-indigo-400'
              }`} />
            </div>
            <div className="flex-1 min-w-0 text-left">
              <p className="text-sm text-white font-medium truncate">
                {selectedBot?.name || 'Select bot'}
              </p>
              <p className={`text-[10px] capitalize ${
                selectedBot?.status === 'draft' ? 'text-amber-400' : 'text-slate-500'
              }`}>
                {selectedBot?.status === 'draft' ? 'Draft' : selectedBot?.status || 'none'} &middot; {selectedBot?.model || ''}
              </p>
            </div>
            <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform ${showBotMenu ? 'rotate-180' : ''}`} />
          </button>

          {showBotMenu && (
            <div className="absolute left-3 right-3 top-full mt-1 bg-slate-700 border border-slate-600 rounded-xl shadow-xl z-20 py-1 max-h-60 overflow-y-auto">
              {bots.map((bot) => (
                <button
                  key={bot.id}
                  onClick={() => { selectBot(bot.id); setShowBotMenu(false); }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-slate-600/50 transition-colors ${
                    selectedBot?.id === bot.id ? 'bg-slate-600/30' : ''
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full shrink-0 ${
                    bot.status === 'online' ? 'bg-emerald-400' :
                    bot.status === 'draft' ? 'bg-amber-400' :
                    'bg-slate-500'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{bot.name}</p>
                    <p className={`text-[10px] capitalize ${
                      bot.status === 'draft' ? 'text-amber-400' : 'text-slate-500'
                    }`}>
                      {bot.status === 'draft' ? 'Draft' : bot.channel || 'no channel'}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-600/15 text-indigo-300'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700/40'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </NavLink>
        ))}

        {/* Activate CTA if in sandbox mode */}
        {!isAuthenticated && bots.some(b => b.status === 'draft') && (
          <Link
            to="/activate"
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium bg-indigo-600/10 text-indigo-300 border border-indigo-500/20 hover:bg-indigo-600/20 transition-colors mt-3"
          >
            <Rocket className="w-5 h-5" />
            Activate Bot
          </Link>
        )}
      </nav>

      {/* User / Account */}
      <div className="px-3 py-4 border-t border-slate-700/50">
        {isAuthenticated ? (
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm text-white font-medium">
              {auth.user?.name?.[0]?.toUpperCase() || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white font-medium truncate">{auth.user?.name}</p>
              <p className="text-xs text-slate-500 truncate">{auth.user?.email}</p>
            </div>
            <button
              onClick={logout}
              className="p-1.5 text-slate-500 hover:text-white transition-colors"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="px-3 py-2">
            <p className="text-xs text-slate-500 mb-2">Sandbox mode — bots saved locally</p>
            <Link
              to="/activate"
              className="block text-center px-3 py-2 bg-indigo-600/20 text-indigo-300 text-sm font-medium rounded-lg hover:bg-indigo-600/30 transition-colors"
            >
              Create Account
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
}
