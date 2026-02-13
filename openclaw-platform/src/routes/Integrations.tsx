import { useState } from 'react';
import { Search } from 'lucide-react';
import { IntegrationCard } from '../components/integrations/IntegrationCard';
import type { Integration } from '../types';
import { useBots } from '../hooks/useBots';

const integrations: Integration[] = [
  // Channels
  { id: 'whatsapp', name: 'WhatsApp', description: 'Most popular messaging app. Respond to messages, send media, manage groups.', icon: '💬', category: 'channel', status: 'available', popular: true },
  { id: 'telegram', name: 'Telegram', description: 'Fast setup. Great for personal bots, inline commands, and media.', icon: '✈️', category: 'channel', status: 'connected', popular: true },
  { id: 'discord', name: 'Discord', description: 'Perfect for communities. Multi-server, threads, reactions.', icon: '🎮', category: 'channel', status: 'available', popular: true },
  { id: 'slack', name: 'Slack', description: 'Workplace integration. Channels, DMs, slash commands.', icon: '💼', category: 'channel', status: 'available' },
  { id: 'signal', name: 'Signal', description: 'Secure private messaging with end-to-end encryption.', icon: '🔒', category: 'channel', status: 'available' },
  { id: 'imessage', name: 'iMessage', description: 'Apple Messages via BlueBubbles. Native feel on iPhone/Mac.', icon: '🍎', category: 'channel', status: 'available' },
  { id: 'webchat', name: 'WebChat', description: 'Built-in browser chat. No setup needed, works instantly.', icon: '🌐', category: 'channel', status: 'connected' },
  { id: 'teams', name: 'Microsoft Teams', description: 'Enterprise workspace integration.', icon: '🏢', category: 'channel', status: 'coming_soon' },

  // Skills
  { id: 'gmail', name: 'Gmail', description: 'Read, send, organize, and draft emails. Inbox management on autopilot.', icon: '📧', category: 'skill', status: 'available', popular: true },
  { id: 'calendar', name: 'Google Calendar', description: 'Check schedule, create events, get reminders. Never miss a meeting.', icon: '📅', category: 'skill', status: 'available', popular: true },
  { id: 'github', name: 'GitHub', description: 'Manage repos, PRs, issues. Code review and deployment automation.', icon: '🐙', category: 'skill', status: 'available' },
  { id: 'browser', name: 'Browser Control', description: 'Browse the web, fill forms, extract data from any site.', icon: '🖥️', category: 'skill', status: 'connected' },

  // Tools
  { id: 'spotify', name: 'Spotify', description: 'Control playback, create playlists, discover music.', icon: '🎵', category: 'tool', status: 'available' },
  { id: 'hue', name: 'Philips Hue', description: 'Smart lights control. Set scenes, schedules, and automations.', icon: '💡', category: 'tool', status: 'available' },
  { id: 'obsidian', name: 'Obsidian', description: 'Second brain integration. Search notes, create entries, link knowledge.', icon: '📝', category: 'tool', status: 'available' },
  { id: 'twitter', name: 'Twitter/X', description: 'Post tweets, monitor mentions, engage with followers.', icon: '🐦', category: 'tool', status: 'coming_soon' },
];

const categories = [
  { id: 'all', label: 'All' },
  { id: 'channel', label: 'Channels' },
  { id: 'skill', label: 'Skills' },
  { id: 'tool', label: 'Tools' },
];

export default function Integrations() {
  const { selectedBot } = useBots();
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');

  const filtered = integrations.filter((i) => {
    const matchesSearch = i.name.toLowerCase().includes(search.toLowerCase()) ||
      i.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = category === 'all' || i.category === category;
    return matchesSearch && matchesCategory;
  });

  const connected = integrations.filter((i) => i.status === 'connected').length;

  return (
    <div className="px-4 sm:px-8 py-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Integrations</h1>
        <p className="text-sm text-slate-400 mt-1">
          {selectedBot && <><span className="text-white font-medium">{selectedBot.name}</span> &middot; </>}
          {connected} connected — {integrations.length - connected} more available
        </p>
      </div>

      {/* Search & filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search integrations..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 transition-all"
          />
        </div>
        <div className="flex gap-2">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setCategory(cat.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                category === cat.id
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                  : 'bg-slate-800/40 text-slate-400 border border-slate-700/40 hover:text-white'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Recommended */}
      {category === 'all' && !search && (
        <div className="mb-8">
          <h2 className="text-sm font-medium text-amber-400 mb-3 flex items-center gap-2">
            ✨ Recommended for you
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {integrations
              .filter((i) => i.popular && i.status === 'available')
              .slice(0, 3)
              .map((i) => (
                <IntegrationCard key={i.id} integration={i} onConnect={() => {}} />
              ))}
          </div>
        </div>
      )}

      {/* All integrations */}
      <div>
        <h2 className="text-sm font-medium text-slate-400 mb-3">
          {category === 'all' ? 'All Integrations' : categories.find((c) => c.id === category)?.label}
          <span className="ml-2 text-slate-500">({filtered.length})</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((i) => (
            <IntegrationCard key={i.id} integration={i} onConnect={() => {}} />
          ))}
        </div>
      </div>
    </div>
  );
}
