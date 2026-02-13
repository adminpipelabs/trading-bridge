import { useState, useEffect } from 'react';
import { Wifi, Battery, Signal, Bot, Send } from 'lucide-react';

const conversation = [
  { role: 'user' as const, text: 'Hey, check my calendar for tomorrow', delay: 0 },
  { role: 'bot' as const, text: 'You have 3 meetings tomorrow:\n\n9:00 AM — Team standup\n11:30 AM — Design review\n2:00 PM — Client call with Acme Corp\n\nWant me to prep notes for any of these?', delay: 800 },
  { role: 'user' as const, text: 'Prep notes for the client call', delay: 2000 },
  { role: 'bot' as const, text: "Done! I've pulled their last 3 emails, the open proposal, and their payment history. Notes are in your Obsidian vault under /clients/acme.", delay: 2800 },
  { role: 'user' as const, text: 'Also send a reminder to the team on Slack', delay: 4200 },
  { role: 'bot' as const, text: 'Sent to #general:\n"Reminder: Client call with Acme Corp at 2 PM tomorrow. Prep notes are ready."\n\n3 people reacted 👍', delay: 5000 },
];

export function BotPreview() {
  const [visibleMessages, setVisibleMessages] = useState(0);

  useEffect(() => {
    if (visibleMessages >= conversation.length) return;

    const nextDelay = visibleMessages === 0
      ? 600
      : (conversation[visibleMessages].delay - conversation[visibleMessages - 1].delay);

    const timer = setTimeout(() => {
      setVisibleMessages((prev) => prev + 1);
    }, nextDelay);

    return () => clearTimeout(timer);
  }, [visibleMessages]);

  return (
    <div className="relative w-full max-w-[340px]">
      {/* Glow behind the phone */}
      <div className="absolute -inset-4 bg-indigo-600/10 rounded-[3rem] blur-2xl" />

      {/* Phone frame */}
      <div className="relative bg-slate-950 rounded-[2.5rem] border border-slate-700/60 shadow-2xl overflow-hidden">
        {/* Notch */}
        <div className="flex justify-center pt-2 pb-0">
          <div className="w-28 h-6 bg-slate-950 rounded-b-2xl" />
        </div>

        {/* Status bar */}
        <div className="flex items-center justify-between px-6 py-1 text-[10px] text-slate-500">
          <span>9:41</span>
          <div className="flex items-center gap-1">
            <Signal className="w-3 h-3" />
            <Wifi className="w-3 h-3" />
            <Battery className="w-3 h-3" />
          </div>
        </div>

        {/* Chat header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800/60">
          <div className="w-9 h-9 rounded-full bg-indigo-600/20 flex items-center justify-center">
            <Bot className="w-5 h-5 text-indigo-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm text-white font-medium">Work Assistant</p>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-[10px] text-emerald-400">Online — 24/7</span>
            </div>
          </div>
          <span className="text-[10px] px-2 py-0.5 bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20">
            Hosted
          </span>
        </div>

        {/* Messages */}
        <div className="px-3 py-4 space-y-3 h-[360px] overflow-hidden">
          {conversation.slice(0, visibleMessages).map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
            >
              <div
                className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-xs leading-relaxed whitespace-pre-line ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-md'
                    : 'bg-slate-800/80 text-slate-200 rounded-bl-md border border-slate-700/30'
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {visibleMessages < conversation.length && visibleMessages > 0 && conversation[visibleMessages].role === 'bot' && (
            <div className="flex justify-start">
              <div className="px-4 py-3 rounded-2xl bg-slate-800/80 border border-slate-700/30 rounded-bl-md">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input bar */}
        <div className="px-3 py-3 border-t border-slate-800/60">
          <div className="flex items-center gap-2 bg-slate-800/50 rounded-full px-4 py-2.5">
            <span className="text-xs text-slate-500 flex-1">Message your bot...</span>
            <Send className="w-4 h-4 text-indigo-400" />
          </div>
        </div>

        {/* Home indicator */}
        <div className="flex justify-center py-2">
          <div className="w-32 h-1 bg-slate-700 rounded-full" />
        </div>
      </div>

      {/* Floating status badges */}
      <div className="absolute -right-3 top-20 bg-slate-800 border border-slate-700/60 rounded-xl px-3 py-2 shadow-xl">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] text-slate-300 font-medium">Uptime 99.9%</span>
        </div>
      </div>
      <div className="absolute -left-3 bottom-32 bg-slate-800 border border-slate-700/60 rounded-xl px-3 py-2 shadow-xl">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-300 font-medium">1,234 msgs today</span>
        </div>
      </div>
    </div>
  );
}
