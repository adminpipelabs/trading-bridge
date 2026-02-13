import { ArrowRight, Zap, Wifi, Clock, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';
import { BotPreview } from './BotPreview';

export function Hero() {
  return (
    <section className="relative overflow-hidden px-4 pt-16 pb-20 sm:pt-24 sm:pb-28">
      {/* Background gradient */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-indigo-600/15 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-purple-600/10 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left — copy */}
          <div className="text-center lg:text-left">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-6 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm">
              <Zap className="w-3.5 h-3.5" />
              Hosted Bot Service — Powered by OpenClaw
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight tracking-tight">
              AI Bots That{' '}
              <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                Never Sleep
              </span>
            </h1>

            <p className="mt-6 text-lg text-slate-400 max-w-xl leading-relaxed">
              Deploy AI bots that run <strong className="text-slate-200">24/7 on cloud infrastructure</strong>.
              No terminal. No server management. Just create, deploy, and monitor
              from your browser — on any device.
            </p>

            {/* Trust signals */}
            <div className="mt-6 flex flex-wrap justify-center lg:justify-start gap-x-6 gap-y-2 text-sm text-slate-500">
              <span className="flex items-center gap-1.5">
                <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                Always online
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                24/7 monitoring
              </span>
              <span className="flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-indigo-400" />
                Your data, your bots
              </span>
            </div>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
              <Link
                to="/onboarding"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-colors text-lg"
              >
                Create Your Bot
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 bg-slate-800/50 hover:bg-slate-700/50 text-slate-300 font-medium rounded-xl border border-slate-700/50 transition-colors text-lg"
              >
                I Have an Account
              </Link>
            </div>

            <p className="mt-4 text-sm text-slate-500">
              No account needed — start building right now
            </p>
          </div>

          {/* Right — bot preview */}
          <div className="flex justify-center lg:justify-end">
            <BotPreview />
          </div>
        </div>
      </div>
    </section>
  );
}
