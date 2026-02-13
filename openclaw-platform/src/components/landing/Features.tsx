import {
  Cloud,
  Activity,
  MessageSquare,
  Puzzle,
  BarChart3,
  Shield,
  Sparkles,
  Zap,
  Users,
} from 'lucide-react';

const features = [
  {
    icon: Cloud,
    title: 'Hosted 24/7',
    description:
      'Your bots run on cloud infrastructure around the clock. No laptop left open, no terminal running overnight. We keep them online.',
  },
  {
    icon: Activity,
    title: 'Live Monitoring',
    description:
      'Real-time health checks, uptime tracking, and alerts. Know instantly if something needs attention — before your users notice.',
  },
  {
    icon: Zap,
    title: '2-Minute Setup',
    description:
      'Name your bot, pick a model, choose a channel. Click deploy. No CLI, no Docker, no config files, no DevOps skills needed.',
  },
  {
    icon: MessageSquare,
    title: 'Any Chat Platform',
    description:
      'WhatsApp, Telegram, Discord, Slack, Signal, iMessage — your bot lives where your users already are. Add channels anytime.',
  },
  {
    icon: Puzzle,
    title: 'Smart Integrations',
    description:
      'Gmail, Calendar, GitHub, Browser, Spotify, and 50+ more. We suggest new integrations based on how people use your bot.',
  },
  {
    icon: BarChart3,
    title: 'Analytics & Insights',
    description:
      'Message volume, response times, user satisfaction, peak hours. AI-powered recommendations to improve performance.',
  },
  {
    icon: Users,
    title: 'Multi-Bot Management',
    description:
      'Run 1 bot or 100 from a single dashboard. Switch between them, compare stats, manage everything from one login.',
  },
  {
    icon: Shield,
    title: 'Your Data, Your Bots',
    description:
      'Built on open-source OpenClaw. Self-hosted on your infrastructure. Your conversations and data never leave your control.',
  },
  {
    icon: Sparkles,
    title: 'Gets Smarter Over Time',
    description:
      'Persistent memory, custom skills, proactive actions. Your bot learns from interactions and adapts to serve users better.',
  },
];

export function Features() {
  return (
    <section className="px-4 py-20 sm:py-28 border-t border-slate-800">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white">
            Not Just Bot Creation.{' '}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Bot Operations.
            </span>
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
            Anyone can spin up a bot. The hard part is keeping it running,
            improving it, and understanding how it's being used. That's what
            BotForge is for.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/30 hover:border-slate-600/50 transition-colors"
            >
              <div className="w-11 h-11 rounded-xl bg-indigo-600/15 flex items-center justify-center mb-4">
                <feature.icon className="w-5 h-5 text-indigo-400" />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
