import { ArrowLeft, Rocket, Check } from 'lucide-react';
import type { OnboardingData } from '../../routes/Onboarding';

interface Props {
  data: OnboardingData;
  onFinish: () => void;
  onBack: () => void;
}

export function DoneStep({ data, onFinish, onBack }: Props) {
  const handleLaunch = () => {
    // Save as draft bot in localStorage (no account needed yet)
    const drafts = JSON.parse(localStorage.getItem('bf-draft-bots') || '[]');
    const draft = {
      id: `draft-${Date.now()}`,
      name: data.botName,
      persona: data.persona,
      model: data.model,
      channel: data.channel,
      status: 'draft',
      created_at: new Date().toISOString(),
    };
    drafts.push(draft);
    localStorage.setItem('bf-draft-bots', JSON.stringify(drafts));
    onFinish();
  };

  return (
    <div>
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-emerald-600/20 mb-4">
          <Check className="w-7 h-7 text-emerald-400" />
        </div>
        <h2 className="text-2xl font-bold text-white">
          {data.botName} is Ready!
        </h2>
        <p className="text-slate-400 mt-2">
          Your bot is configured. Preview it in the dashboard, tweak settings,
          and activate when you're ready.
        </p>
      </div>

      {/* Bot summary */}
      <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-4 mb-6 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Bot Name</span>
          <span className="text-white font-medium">{data.botName}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Personality</span>
          <span className="text-white font-medium capitalize">{data.persona}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Model</span>
          <span className="text-white font-medium capitalize">{data.model}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Channel</span>
          <span className="text-white font-medium capitalize">{data.channel}</span>
        </div>
      </div>

      {/* What happens next */}
      <div className="bg-indigo-500/5 border border-indigo-500/15 rounded-xl p-4 mb-6">
        <p className="text-sm font-medium text-indigo-300 mb-2">What happens next?</p>
        <ul className="space-y-1.5 text-xs text-slate-400">
          <li className="flex items-start gap-2">
            <span className="text-indigo-400 mt-0.5">1.</span>
            Preview your bot in the dashboard
          </li>
          <li className="flex items-start gap-2">
            <span className="text-indigo-400 mt-0.5">2.</span>
            Adjust settings, integrations, and system prompt
          </li>
          <li className="flex items-start gap-2">
            <span className="text-indigo-400 mt-0.5">3.</span>
            When ready, hit <strong className="text-white">Activate</strong> to make it live 24/7
          </li>
        </ul>
      </div>

      <div className="flex gap-3">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-3 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <button
          onClick={handleLaunch}
          className="flex-1 inline-flex items-center justify-center gap-2 py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition-colors"
        >
          <Rocket className="w-4 h-4" />
          Go to Dashboard
        </button>
      </div>

      <p className="text-center text-xs text-slate-500 mt-4">
        No account needed — explore everything first
      </p>
    </div>
  );
}
