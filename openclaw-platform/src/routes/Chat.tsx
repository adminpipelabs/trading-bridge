import { useEffect } from 'react';
import { useGateway } from '../hooks/useGateway';
import { ChatView } from '../components/chat/ChatView';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import { useBots } from '../hooks/useBots';

// Gateway config — in production this comes from backend/env
const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://5.161.64.209:18789';
const GATEWAY_TOKEN = import.meta.env.VITE_GATEWAY_TOKEN || '';

export default function Chat() {
  const { messages, connection, isStreaming, connect, sendMessage, abortChat } = useGateway();
  const { selectedBot } = useBots();

  useEffect(() => {
    if (connection.status === 'disconnected' && GATEWAY_TOKEN) {
      connect(GATEWAY_URL, GATEWAY_TOKEN);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="h-full flex flex-col">
      {/* Status bar */}
      <div className="flex items-center justify-between px-4 sm:px-8 py-3 border-b border-slate-700/50">
        <div>
          <h1 className="text-lg font-semibold text-white">
            Chat{selectedBot ? ` — ${selectedBot.name}` : ''}
          </h1>
          <p className="text-xs text-slate-400">Talk to your bot live</p>
        </div>
        <div className="flex items-center gap-2">
          {connection.status === 'connected' && (
            <div className="flex items-center gap-1.5 text-emerald-400 text-xs">
              <Wifi className="w-3.5 h-3.5" />
              Connected
            </div>
          )}
          {connection.status === 'connecting' && (
            <div className="flex items-center gap-1.5 text-amber-400 text-xs">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Connecting...
            </div>
          )}
          {(connection.status === 'disconnected' || connection.status === 'error') && (
            <div className="flex items-center gap-1.5 text-red-400 text-xs">
              <WifiOff className="w-3.5 h-3.5" />
              {connection.error || 'Disconnected'}
            </div>
          )}
        </div>
      </div>

      {/* Chat area */}
      {connection.status === 'connected' ? (
        <div className="flex-1 min-h-0">
          <ChatView
            messages={messages}
            isStreaming={isStreaming}
            onSend={sendMessage}
            onAbort={abortChat}
          />
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center px-8">
          <div className="text-center">
            {connection.status === 'connecting' ? (
              <>
                <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
                <p className="text-slate-400">Connecting to gateway...</p>
              </>
            ) : (
              <>
                <WifiOff className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400 mb-4">
                  {connection.error || 'Configure your gateway connection to start chatting.'}
                </p>
                {GATEWAY_TOKEN && (
                  <button
                    onClick={() => connect(GATEWAY_URL, GATEWAY_TOKEN)}
                    className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    Reconnect
                  </button>
                )}
                {!GATEWAY_TOKEN && (
                  <p className="text-xs text-slate-500">
                    Set VITE_GATEWAY_URL and VITE_GATEWAY_TOKEN in your environment
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
