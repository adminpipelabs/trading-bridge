import { Link } from 'react-router-dom';
import { Lightbulb, ArrowRight } from 'lucide-react';
import type { Opportunity } from '../../types';

const opportunities: Opportunity[] = [
  {
    id: '1',
    type: 'integration',
    title: 'Connect Gmail',
    description:
      'Your bot could manage your inbox — read, reply, and organize emails automatically.',
    actionLabel: 'Set up Gmail',
    actionUrl: '/integrations',
    priority: 'high',
  },
  {
    id: '2',
    type: 'skill',
    title: 'Enable Calendar Skill',
    description:
      'Users ask about scheduling 40% of the time. The Calendar skill handles it automatically.',
    actionLabel: 'Enable skill',
    actionUrl: '/integrations',
    priority: 'high',
  },
  {
    id: '3',
    type: 'integration',
    title: 'Add Telegram',
    description:
      'Telegram bots are the fastest to set up — most users see 3x more engagement there.',
    actionLabel: 'Connect Telegram',
    actionUrl: '/integrations',
    priority: 'medium',
  },
  {
    id: '4',
    type: 'optimization',
    title: 'Set Up Heartbeats',
    description:
      'Let your bot proactively reach out with daily briefings, reminders, and check-ins.',
    actionLabel: 'Configure',
    actionUrl: '/settings',
    priority: 'medium',
  },
];

const priorityColors = {
  high: 'border-l-indigo-500',
  medium: 'border-l-amber-500',
  low: 'border-l-slate-500',
};

export function OpportunityCards() {
  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="w-5 h-5 text-amber-400" />
        <h3 className="text-white font-semibold">Opportunities</h3>
        <span className="text-xs bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full">
          {opportunities.length} suggestions
        </span>
      </div>

      <div className="space-y-3">
        {opportunities.map((opp) => (
          <div
            key={opp.id}
            className={`bg-slate-800/30 border border-slate-700/30 border-l-2 ${priorityColors[opp.priority]} rounded-xl p-4`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-white">{opp.title}</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  {opp.description}
                </p>
              </div>
              <Link
                to={opp.actionUrl}
                className="shrink-0 flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
              >
                {opp.actionLabel}
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
