import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Check, ArrowLeft, Rocket, Shield, Crown } from 'lucide-react';
import { useBots } from '../hooks/useBots';
import { api } from '../api/client';

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'forever',
    icon: Zap,
    color: 'slate',
    description: 'Try it out. One bot, basic monitoring.',
    features: [
      '1 active bot',
      '500 messages / month',
      'Basic analytics',
      'Community support',
      'WebChat channel',
    ],
    limits: [
      'No Telegram/WhatsApp',
      'No advanced integrations',
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
    features: [
      'Up to 5 active bots',
      '10,000 messages / month',
      'Full analytics & insights',
      'All channels (Telegram, WhatsApp, Discord...)',
      'All integrations (Gmail, Calendar, GitHub...)',
      'Email support',
      'Auto-restart & health monitoring',
    ],
    limits: [],
  },
  {
    id: 'business',
    name: 'Business',
    price: '$49',
    period: '/month',
    icon: Crown,
    color: 'purple',
    description: 'For teams and power users.',
    features: [
      'Unlimited active bots',
      'Unlimited messages',
      'Priority support + SLA',
      'Custom integrations',
      'API access',
      'Team members (coming soon)',
      'Advanced analytics & exports',
    ],
    limits: [],
  },
];

export default function Activate() {
  const navigate = useNavigate();
  const { selectedBot, refresh } = useBots();
  const [selectedPlan, setSelectedPlan] = useState('free');
  const [step, setStep] = useState<'plan' | 'account'>('plan');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const isLoggedIn = !!localStorage.getItem('bf-token');

  const handleSelectPlan = (planId: string) => {
    setSelectedPlan(planId);
  };

  const handleContinue = () => {
    if (isLoggedIn) {
      // Already logged in — just activate
      handleActivate();
    } else {
      setStep('account');
    }
  };

  const handleActivate = async () => {
    setError('');
    setLoading(true);

    try {
      // Create account if needed
      if (!isLoggedIn) {
        if (!email.trim() || !password.trim()) {
          setError('Email and password are required');
          setLoading(false);
          return;
        }
        if (password.length < 8) {
          setError('Password must be at least 8 characters');
          setLoading(false);
          return;
        }

        const res = await api.post('/api/auth/signup', {
          name: selectedBot?.name || 'Bot Owner',
          email: email.trim(),
          password,
        });
        const { token, user } = res as { token: string; user: { id: string; name: string; email: string } };
        localStorage.setItem('bf-token', token);
        localStorage.setItem('bf-user', JSON.stringify(user));
      }

      // Migrate all draft bots to the real account
      const drafts = JSON.parse(localStorage.getItem('bf-draft-bots') || '[]');
      for (const draft of drafts) {
        await api.post('/api/bots', {
          name: draft.name,
          persona: draft.persona,
          model: draft.model,
          channel: draft.channel,
          system_prompt: draft.system_prompt || '',
        });
      }

      // Clear drafts
      localStorage.removeItem('bf-draft-bots');

      // Update the first default bot created on signup (if it exists) to match
      // Actually the drafts are now saved as real bots, and signup creates a default.
      // Let's clean up by deleting the auto-created default if we migrated drafts
      if (drafts.length > 0) {
        const botsRes = await api.get('/api/bots') as { bots: Array<{ id: string; name: string }> };
        // The auto-created bot from signup has a name like "Bot Owner's Bot"
        const autoBot = botsRes.bots.find(b => b.name.includes("'s Bot"));
        if (autoBot) {
          await api.delete(`/api/bots/${autoBot.id}`);
        }
      }

      await refresh();
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  if (!selectedBot) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        No bot to activate. Go create one first.
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-8 py-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => step === 'account' ? setStep('plan') : navigate('/dashboard')}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          {step === 'account' ? 'Back to plans' : 'Back to dashboard'}
        </button>
        <h1 className="text-2xl font-bold text-white">
          Activate {selectedBot.name}
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          {step === 'plan'
            ? 'Choose a plan to make your bot live 24/7 with monitoring and full features.'
            : 'Create your account to claim this bot.'}
        </p>
      </div>

      {step === 'plan' ? (
        <>
          {/* Pricing cards */}
          <div className="grid md:grid-cols-3 gap-5 mb-8">
            {plans.map((plan) => {
              const isSelected = selectedPlan === plan.id;
              return (
                <div
                  key={plan.id}
                  onClick={() => handleSelectPlan(plan.id)}
                  className={`relative cursor-pointer rounded-2xl p-6 border transition-all ${
                    isSelected
                      ? 'bg-slate-800/60 border-indigo-500/50 ring-1 ring-indigo-500/20'
                      : 'bg-slate-800/30 border-slate-700/40 hover:border-slate-600/60'
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
                      <div className="flex items-baseline gap-0.5">
                        <span className="text-2xl font-bold text-white">{plan.price}</span>
                        <span className="text-sm text-slate-500">{plan.period}</span>
                      </div>
                    </div>
                  </div>

                  <p className="text-sm text-slate-400 mb-4">{plan.description}</p>

                  <ul className="space-y-2 mb-4">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                        <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        {f}
                      </li>
                    ))}
                    {plan.limits.map((l) => (
                      <li key={l} className="flex items-start gap-2 text-sm text-slate-500">
                        <span className="w-4 text-center shrink-0 mt-0.5">—</span>
                        {l}
                      </li>
                    ))}
                  </ul>

                  {isSelected && (
                    <div className="absolute top-3 right-3 w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center">
                      <Check className="w-3.5 h-3.5 text-white" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Cost summary */}
          <div className="bg-slate-800/30 border border-slate-700/40 rounded-xl p-5 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Monthly cost for {selectedBot.name}</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {plans.find(p => p.id === selectedPlan)?.price}
                  <span className="text-sm text-slate-500 font-normal ml-1">
                    {plans.find(p => p.id === selectedPlan)?.period}
                  </span>
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-500">Includes</p>
                <p className="text-xs text-slate-400">
                  24/7 hosting, monitoring, auto-restart
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={handleContinue}
            className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition-colors text-base"
          >
            <Rocket className="w-5 h-5" />
            {isLoggedIn ? 'Activate Bot' : `Continue with ${plans.find(p => p.id === selectedPlan)?.name} Plan`}
          </button>

          {selectedPlan === 'free' && (
            <p className="text-center text-xs text-slate-500 mt-3">
              No credit card required. Upgrade anytime.
            </p>
          )}
        </>
      ) : (
        /* Account creation step */
        <div className="max-w-md mx-auto">
          <div className="bg-slate-800/40 border border-slate-700/40 rounded-2xl p-6 mb-6">
            <h3 className="text-white font-semibold mb-1">
              Claim Your Bot
            </h3>
            <p className="text-sm text-slate-400 mb-5">
              Create an account to own this bot. All your draft bots will be saved.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  disabled={loading}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1.5">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 8 characters"
                  className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  disabled={loading}
                />
              </div>
            </div>
          </div>

          {/* Plan summary */}
          <div className="bg-indigo-500/5 border border-indigo-500/15 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Plan</span>
              <span className="text-white font-medium capitalize">{selectedPlan}</span>
            </div>
            <div className="flex items-center justify-between text-sm mt-1">
              <span className="text-slate-400">Bot</span>
              <span className="text-white font-medium">{selectedBot.name}</span>
            </div>
            <div className="flex items-center justify-between text-sm mt-1">
              <span className="text-slate-400">Cost</span>
              <span className="text-white font-medium">
                {plans.find(p => p.id === selectedPlan)?.price} {plans.find(p => p.id === selectedPlan)?.period}
              </span>
            </div>
          </div>

          {error && (
            <div className="px-4 py-2 mb-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            onClick={handleActivate}
            disabled={loading || !email.trim() || !password.trim()}
            className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-xl transition-colors"
          >
            <Rocket className="w-5 h-5" />
            {loading ? 'Activating...' : 'Create Account & Activate'}
          </button>

          <p className="text-center text-xs text-slate-500 mt-3">
            Already have an account?{' '}
            <button
              onClick={() => navigate('/login')}
              className="text-indigo-400 hover:text-indigo-300 underline"
            >
              Sign in
            </button>
          </p>
        </div>
      )}
    </div>
  );
}
