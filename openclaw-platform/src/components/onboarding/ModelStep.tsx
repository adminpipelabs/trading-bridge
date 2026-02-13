import { ArrowLeft } from 'lucide-react';
import type { OnboardingData } from '../../routes/Onboarding';

const models = [
  {
    id: 'anthropic',
    name: 'Anthropic (Claude)',
    desc: 'Best for complex tasks, long context, and coding. Recommended.',
    badge: 'Recommended',
  },
  {
    id: 'openai',
    name: 'OpenAI (GPT)',
    desc: 'Great general-purpose model with wide capabilities.',
    badge: null,
  },
  {
    id: 'local',
    name: 'Local / OpenRouter',
    desc: 'Run open models locally or via OpenRouter. Full privacy.',
    badge: 'Advanced',
  },
];

interface Props {
  data: OnboardingData;
  update: (partial: Partial<OnboardingData>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function ModelStep({ data, update, onNext, onBack }: Props) {
  return (
    <div>
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-white">Choose Your Model</h2>
        <p className="text-slate-400 mt-2">
          Which AI provider should power your bot? You can change this later.
        </p>
      </div>

      <div className="space-y-3">
        {models.map((m) => (
          <button
            key={m.id}
            onClick={() => update({ model: m.id })}
            className={`w-full p-4 rounded-xl border text-left transition-all ${
              data.model === m.id
                ? 'bg-indigo-600/15 border-indigo-500/50'
                : 'bg-slate-800/30 border-slate-700/40 hover:border-slate-600/60'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className={`font-medium ${data.model === m.id ? 'text-indigo-300' : 'text-white'}`}>
                {m.name}
              </span>
              {m.badge && (
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  m.badge === 'Recommended'
                    ? 'bg-indigo-500/20 text-indigo-300'
                    : 'bg-slate-700/50 text-slate-400'
                }`}>
                  {m.badge}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400 mt-1">{m.desc}</p>
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
          className="flex-1 py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition-colors"
        >
          Continue
        </button>
      </div>
    </div>
  );
}
