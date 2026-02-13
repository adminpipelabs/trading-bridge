import { useEffect, useRef } from 'react';
import type { Message } from '../../types';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { MessageSquare } from 'lucide-react';

interface Props {
  messages: Message[];
  isStreaming: boolean;
  onSend: (message: string) => void;
  onAbort: () => void;
}

export function ChatView({ messages, isStreaming, onSend, onAbort }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div ref={scrollRef} className="flex-1 overflow-y-auto py-4 space-y-1">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 px-8">
            <MessageSquare className="w-12 h-12 mb-3 text-slate-600" />
            <p className="text-center text-sm">Send a message to start chatting with your bot</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>
      <ChatInput onSend={onSend} onAbort={onAbort} isStreaming={isStreaming} disabled={false} />
    </div>
  );
}
