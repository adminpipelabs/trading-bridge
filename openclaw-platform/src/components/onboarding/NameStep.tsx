import { Bot, Smile, Briefcase, Coffee } from 'lucide-react';
import type { OnboardingData } from '../../routes/Onboarding';

const personas = [
  { id: 'friendly', label: 'Friendly', icon: Smile, desc: 'Warm and conversational' },
  { id: 'professional', label: 'Professional', icon: Briefcase, desc: 'Formal and precise' },
  { id: 'casual', label: 'Casual', icon: Coffee, desc: 'Relaxed and witty' },
];

interface Props {
  data: OnboardingData;
  update: (partial: Partial<OnboardingData>) => void;
  onNext: () => void;
}

export function NameStep({ data, update, onNext }: Props) {
  const canProceed = data.botName.trim().length >= 2;

  return (
    <div>
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-600/20 mb-4">
          <Bot className="w-7 h-7 text-indigo-400" />
        </div>
        <h2 className="text-2xl font-bold text-white">Name Your Bot</h2>
        <p className="text-slate-400 mt-2">Give it a personality and make it yours.</p>
      </div>

      <div className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">Bot Name</label>
          <input
            type="text"
            value={data.botName}
            onChange={(e) => update({ botName: e.target.value })}
            placeholder="e.g. Jarvis, Friday, Molly..."
            className="w-full px-4 py-3 bg-slate-800/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
            autoFocus
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-3">Personality</label>
          <div className="grid grid-cols-3 gap-3">
            {personas.map((p) => (
              <button
                key={p.id}
                onClick={() => update({ persona: p.id })}
                className={`p-4 rounded-xl border text-center transition-all ${
                  data.persona === p.id
                    ? 'bg-indigo-600/15 border-indigo-500/50 text-indigo-300'
                    : 'bg-slate-800/30 border-slate-700/40 text-slate-400 hover:border-slate-600/60'
                }`}
              >
                <p.icon className="w-5 h-5 mx-auto mb-2" />
                <span className="text-sm font-medium">{p.label}</span>
                <span className="block text-xs mt-0.5 opacity-60">{p.desc}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <button
        onClick={onNext}
        disabled={!canProceed}
        className="w-full mt-8 py-3 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-xl transition-colors"
      >
        Continue
      </button>
    </div>
  );
}
