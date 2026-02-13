import { Check, Zap, Shield, Crown } from 'lucide-react';
import { Link } from 'react-router-dom';

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'forever',
    icon: Zap,
    color: 'slate',
    description: 'Try it out. One bot, basic monitoring.',
    cta: 'Start Free',
    features: [
      '1 active bot',
      '500 messages / month',
      'Basic analytics',
      'WebChat channel',
      'Community support',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$19',
    period: '/month',
    icon: Shield,
    color: 'indigo',
    popular: true,
    description: 'For builders running real bots.',
    cta: 'Start Building',
    features: [
      'Up to 5 active bots',
      '10,000 messages / month',
      'Full analytics & AI insights',
      'All channels (Telegram, WhatsApp, Discord...)',
      'All integrations (Gmail, Calendar, GitHub...)',
      'Auto-restart & health monitoring',
      'Email support',
    ],
  },
  {
    id: 'business',
    name: 'Business',
    price: '$49',
    period: '/month',
    icon: Crown,
    color: 'purple',
    description: 'For teams and power users.',
    cta: 'Contact Us',
    features: [
      'Unlimited active bots',
      'Unlimited messages',
      'Priority support + SLA',
      'Custom integrations',
      'API access',
      'Team members (coming soon)',
      'Advanced analytics & data exports',
    ],
  },
];

export function Pricing() {
  return (
    <section className="px-4 py-20 sm:py-28 border-t border-slate-800" id="pricing">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-white">
            Simple, Transparent Pricing
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
            Creation is always free. You pay for keeping bots running 24/7
            with monitoring, analytics, and integrations.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`relative rounded-2xl p-6 border transition-colors ${
                plan.popular
                  ? 'bg-slate-800/50 border-indigo-500/30 ring-1 ring-indigo-500/10'
                  : 'bg-slate-800/30 border-slate-700/40'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-indigo-600 text-white text-xs font-medium rounded-full">
                  Most Popular
                </div>
              )}

              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  plan.color === 'indigo' ? 'bg-indigo-600/15' :
                  plan.color === 'purple' ? 'bg-purple-600/15' :
                  'bg-slate-700/30'
                }`}>
                  <plan.icon className={`w-5 h-5 ${
                    plan.color === 'indigo' ? 'text-indigo-400' :
                    plan.color === 'purple' ? 'text-purple-400' :
                    'text-slate-400'
                  }`} />
                </div>
                <div>
                  <h3 className="text-white font-semibold">{plan.name}</h3>
                </div>
              </div>

              <div className="flex items-baseline gap-0.5 mb-2">
                <span className="text-3xl font-bold text-white">{plan.price}</span>
                <span className="text-sm text-slate-500">{plan.period}</span>
              </div>

              <p className="text-sm text-slate-400 mb-6">{plan.description}</p>

              <ul className="space-y-2.5 mb-6">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                    <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                to="/onboarding"
                className={`block text-center py-3 rounded-xl text-sm font-medium transition-colors ${
                  plan.popular
                    ? 'bg-indigo-600 hover:bg-indigo-500 text-white'
                    : 'bg-slate-700/50 hover:bg-slate-700 text-slate-300 border border-slate-600/40'
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-slate-500 mt-8">
          All plans include 24/7 hosting, auto-restart, and health monitoring.
          No credit card needed to start.
        </p>
      </div>
    </section>
  );
}
