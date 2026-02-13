import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { Hero } from '../components/landing/Hero';
import { HowItWorks } from '../components/landing/HowItWorks';
import { DashboardPreview } from '../components/landing/DashboardPreview';
import { Features } from '../components/landing/Features';
import { Pricing } from '../components/landing/Pricing';
import { Testimonials } from '../components/landing/Testimonials';

export default function Landing() {
  return (
    <div className="min-h-full bg-slate-900">
      {/* Nav */}
      <nav className="flex items-center justify-between px-4 sm:px-8 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
            B
          </div>
          <span className="text-white font-semibold text-lg">BotForge</span>
        </div>
        <div className="flex items-center gap-3">
          <a
            href="#pricing"
            className="hidden sm:inline px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
          >
            Pricing
          </a>
          <Link
            to="/login"
            className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors"
          >
            Sign In
          </Link>
          <Link
            to="/onboarding"
            className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
          >
            Create a Bot
          </Link>
        </div>
      </nav>

      <Hero />
      <HowItWorks />
      <DashboardPreview />
      <Features />

      {/* Channels strip */}
      <section className="px-4 py-16 border-t border-slate-800">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-sm text-slate-500 mb-3 uppercase tracking-wider font-medium">
            Connects to everything
          </p>
          <p className="text-slate-400 text-sm mb-6 max-w-lg mx-auto">
            Your bot talks to the services you already use. Add new channels and skills anytime — no restart needed.
          </p>
          <div className="flex flex-wrap justify-center gap-3 text-slate-400 text-sm">
            {[
              'WhatsApp', 'Telegram', 'Discord', 'Slack', 'Signal',
              'iMessage', 'Gmail', 'GitHub', 'Calendar', 'Browser',
              'Spotify', 'Obsidian', 'Twitter',
            ].map((name) => (
              <span
                key={name}
                className="px-4 py-2 rounded-full bg-slate-800/50 border border-slate-700/30"
              >
                {name}
              </span>
            ))}
            <span className="px-4 py-2 rounded-full bg-slate-800/50 border border-slate-700/30 text-indigo-400">
              50+ more
            </span>
          </div>
        </div>
      </section>

      <Pricing />
      <Testimonials />

      {/* Comparison: Terminal vs BotForge */}
      <section className="px-4 py-20 sm:py-28 border-t border-slate-800">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white">
              Stop Running Bots From a Terminal
            </h2>
            <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
              Most people run bots in a terminal window that dies when their laptop sleeps.
              That's not a service — it's a hack.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-6">
            {/* The Old Way */}
            <div className="p-6 rounded-2xl bg-red-500/5 border border-red-500/15">
              <h3 className="text-red-400 font-semibold mb-4 text-sm uppercase tracking-wider">
                The Terminal Way
              </h3>
              <ul className="space-y-3 text-sm text-slate-400">
                {[
                  'SSH into server, run command manually',
                  'Bot dies when terminal closes',
                  'No monitoring or alerts',
                  'One bot per terminal session',
                  'No analytics or insights',
                  'Restart after every crash by hand',
                  'Config files and environment variables',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <span className="text-red-400/60 mt-0.5">✕</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* The BotForge Way */}
            <div className="p-6 rounded-2xl bg-emerald-500/5 border border-emerald-500/15">
              <h3 className="text-emerald-400 font-semibold mb-4 text-sm uppercase tracking-wider">
                The BotForge Way
              </h3>
              <ul className="space-y-3 text-sm text-slate-300">
                {[
                  'Click "Create Bot" — deployed in seconds',
                  'Runs 24/7 on cloud infrastructure',
                  'Live health monitoring & uptime alerts',
                  'Manage 100 bots from one dashboard',
                  'Built-in analytics and AI insights',
                  'Auto-restart, auto-recover, zero downtime',
                  'Visual config — no files, no code',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 py-20 sm:py-28 border-t border-slate-800">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Your Bots Deserve Better Than a Terminal
          </h2>
          <p className="text-lg text-slate-400 mb-8 max-w-xl mx-auto">
            Create your first bot in 2 minutes. It runs 24/7 with monitoring,
            analytics, and integrations — while you focus on what matters.
          </p>
          <Link
            to="/onboarding"
            className="inline-flex items-center gap-2 px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-colors text-lg"
          >
            Start Building — Free
            <ArrowRight className="w-5 h-5" />
          </Link>
          <p className="text-sm text-slate-500 mt-4">
            No credit card. No setup fee. Build first, decide later.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-4 py-8 border-t border-slate-800">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
          <span>BotForge — Hosted Bot Service powered by OpenClaw</span>
          <div className="flex gap-6">
            <a href="https://github.com/openclaw/openclaw" target="_blank" rel="noopener" className="hover:text-slate-300 transition-colors">
              GitHub
            </a>
            <a href="https://docs.openclaw.ai" target="_blank" rel="noopener" className="hover:text-slate-300 transition-colors">
              Docs
            </a>
            <a href="https://discord.gg/clawd" target="_blank" rel="noopener" className="hover:text-slate-300 transition-colors">
              Discord
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
