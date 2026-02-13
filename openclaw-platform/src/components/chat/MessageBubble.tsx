import type { Message } from '../../types';

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center my-2 px-4">
        <div className="px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400 text-sm max-w-[85%]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-4 my-1`}>
      <div
        className={`max-w-[85%] sm:max-w-[70%] px-4 py-2.5 rounded-2xl ${
          isUser
            ? 'bg-indigo-600 text-white rounded-br-md'
            : 'bg-slate-700/70 text-slate-100 rounded-bl-md'
        }`}
      >
        <div className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">
          {message.content}
          {message.streaming && (
            <span className="inline-block w-1.5 h-4 bg-current opacity-70 animate-pulse ml-0.5 align-text-bottom rounded-sm" />
          )}
        </div>
        <div className={`text-[10px] mt-1 ${isUser ? 'text-indigo-200/50' : 'text-slate-400/50'}`}>
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
