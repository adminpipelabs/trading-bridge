import { ArrowLeft } from 'lucide-react';
import type { OnboardingData } from '../../routes/Onboarding';

const channels = [
  { id: 'telegram', name: 'Telegram', desc: 'Easy setup, great for personal use' },
  { id: 'whatsapp', name: 'WhatsApp', desc: 'Most popular messaging app worldwide' },
  { id: 'discord', name: 'Discord', desc: 'Perfect for communities and teams' },
  { id: 'slack', name: 'Slack', desc: 'Best for workplace and productivity' },
  { id: 'webchat', name: 'WebChat', desc: 'Built-in browser chat — no setup needed' },
  { id: 'signal', name: 'Signal', desc: 'Secure and private messaging' },
];

interface Props {
  data: OnboardingData;
  update: (partial: Partial<OnboardingData>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function ChannelStep({ data, update, onNext, onBack }: Props) {
  return (
    <div>
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-white">Connect a Channel</h2>
        <p className="text-slate-400 mt-2">
          Where should your bot live? Pick one to start — add more later.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {channels.map((ch) => (
          <button
            key={ch.id}
            onClick={() => update({ channel: ch.id })}
            className={`p-4 rounded-xl border text-left transition-all ${
              data.channel === ch.id
                ? 'bg-indigo-600/15 border-indigo-500/50'
                : 'bg-slate-800/30 border-slate-700/40 hover:border-slate-600/60'
            }`}
          >
            <span className={`text-sm font-medium block ${
              data.channel === ch.id ? 'text-indigo-300' : 'text-white'
            }`}>
              {ch.name}
            </span>
            <span className="text-xs text-slate-400 mt-0.5 block">{ch.desc}</span>
          </button>
        ))}
      </div>

      <div className="flex gap-3 mt-8">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-3 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <button
          onClick={onNext}
          disabled={!data.channel}
          className="flex-1 py-3 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-xl transition-colors"
        >
          Continue
        </button>
      </div>
    </div>
  );
}
