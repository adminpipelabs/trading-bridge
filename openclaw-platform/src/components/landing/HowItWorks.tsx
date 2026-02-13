import { Wand2, Rocket, BarChart3, ArrowRight } from 'lucide-react';

const steps = [
  {
    number: '01',
    icon: Wand2,
    title: 'Configure',
    description: 'Name your bot, choose an AI model, pick a personality. Takes about 2 minutes.',
    detail: 'No code, no YAML, no Docker commands.',
    color: 'indigo',
  },
  {
    number: '02',
    icon: Rocket,
    title: 'Deploy',
    description: 'We spin up your bot on always-on cloud infrastructure. It starts running immediately.',
    detail: 'Hosted 24/7. Survives reboots, outages, and updates.',
    color: 'purple',
  },
  {
    number: '03',
    icon: BarChart3,
    title: 'Monitor & Grow',
    description: 'Track messages, response times, user satisfaction. Get AI-powered suggestions to improve.',
    detail: 'Analytics dashboard. Integration recommendations. Zero maintenance.',
    color: 'emerald',
  },
];

const colorMap = {
  indigo: { bg: 'bg-indigo-600/15', text: 'text-indigo-400', border: 'border-indigo-500/20' },
  purple: { bg: 'bg-purple-600/15', text: 'text-purple-400', border: 'border-purple-500/20' },
  emerald: { bg: 'bg-emerald-600/15', text: 'text-emerald-400', border: 'border-emerald-500/20' },
};

export function HowItWorks() {
  return (
    <section className="px-4 py-20 sm:py-28 border-t border-slate-800">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white">
            From Zero to Running Bot in 3 Steps
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
            No servers to manage. No terminals to babysit. Your bot runs on our
            infrastructure while you sleep.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {steps.map((step, i) => {
            const colors = colorMap[step.color as keyof typeof colorMap];
            return (
              <div key={step.number} className="relative">
                {/* Connector arrow (desktop) */}
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-12 -right-3 z-10">
                    <ArrowRight className="w-6 h-6 text-slate-700" />
                  </div>
                )}

                <div className={`h-full p-6 rounded-2xl bg-slate-800/30 border ${colors.border} hover:bg-slate-800/50 transition-colors`}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-12 h-12 rounded-xl ${colors.bg} flex items-center justify-center`}>
                      <step.icon className={`w-6 h-6 ${colors.text}`} />
                    </div>
                    <span className={`text-xs font-bold ${colors.text} uppercase tracking-wider`}>
                      Step {step.number}
                    </span>
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">{step.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed mb-3">
                    {step.description}
                  </p>
                  <p className="text-xs text-slate-500 italic">
                    {step.detail}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
