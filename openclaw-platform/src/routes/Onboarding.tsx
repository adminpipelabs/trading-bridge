import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { NameStep } from '../components/onboarding/NameStep';
import { ModelStep } from '../components/onboarding/ModelStep';
import { ChannelStep } from '../components/onboarding/ChannelStep';
import { DoneStep } from '../components/onboarding/DoneStep';

export interface OnboardingData {
  botName: string;
  persona: string;
  model: string;
  channel: string;
}

const STEPS = ['Name', 'Model', 'Channel', 'Done'] as const;

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [data, setData] = useState<OnboardingData>({
    botName: '',
    persona: 'friendly',
    model: 'anthropic',
    channel: '',
  });

  const update = (partial: Partial<OnboardingData>) => {
    setData((prev) => ({ ...prev, ...partial }));
  };

  const next = () => {
    if (step < STEPS.length - 1) setStep(step + 1);
  };

  const back = () => {
    if (step > 0) setStep(step - 1);
  };

  const finish = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-full flex flex-col bg-slate-900">
      {/* Progress bar */}
      <div className="px-4 pt-6 pb-2 max-w-lg mx-auto w-full">
        <div className="flex gap-2">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                i <= step ? 'bg-indigo-500' : 'bg-slate-700'
              }`}
            />
          ))}
        </div>
        <p className="text-slate-500 text-xs mt-2">
          Step {step + 1} of {STEPS.length}
        </p>
      </div>

      {/* Step content */}
      <div className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-lg">
          {step === 0 && <NameStep data={data} update={update} onNext={next} />}
          {step === 1 && <ModelStep data={data} update={update} onNext={next} onBack={back} />}
          {step === 2 && <ChannelStep data={data} update={update} onNext={next} onBack={back} />}
          {step === 3 && <DoneStep data={data} onFinish={finish} onBack={back} />}
        </div>
      </div>
    </div>
  );
}
