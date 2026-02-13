import { useState } from 'react';
import type { ConnectionState } from '../types';

interface LoginScreenProps {
  onConnect: (gatewayUrl: string, token: string) => void;
  connection: ConnectionState;
}

export function LoginScreen({ onConnect, connection }: LoginScreenProps) {
  const [gatewayUrl, setGatewayUrl] = useState(
    () => localStorage.getItem('oc-gateway-url') || ''
  );
  const [token, setToken] = useState(
    () => localStorage.getItem('oc-token') || ''
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!gatewayUrl.trim() || !token.trim()) return;

    localStorage.setItem('oc-gateway-url', gatewayUrl.trim());
    localStorage.setItem('oc-token', token.trim());
    onConnect(gatewayUrl.trim(), token.trim());
  };

  const isConnecting = connection.status === 'connecting';

  return (
    <div className="min-h-full flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 mb-4">
            <svg className="w-8 h-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">OpenClaw Chat</h1>
          <p className="text-slate-400 mt-1">Connect to your gateway</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-2xl p-6 space-y-4">
          <div>
            <label htmlFor="gateway-url" className="block text-sm font-medium text-slate-300 mb-1.5">
              Gateway URL
            </label>
            <input
              id="gateway-url"
              type="text"
              value={gatewayUrl}
              onChange={(e) => setGatewayUrl(e.target.value)}
              placeholder="http://5.161.64.209:18789"
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
              disabled={isConnecting}
            />
          </div>

          <div>
            <label htmlFor="token" className="block text-sm font-medium text-slate-300 mb-1.5">
              Gateway Token
            </label>
            <input
              id="token"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Your gateway token"
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
              disabled={isConnecting}
            />
          </div>

          {connection.error && (
            <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
              {connection.error}
            </div>
          )}

          <button
            type="submit"
            disabled={isConnecting || !gatewayUrl.trim() || !token.trim()}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-xl transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          >
            {isConnecting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Connecting...
              </span>
            ) : (
              'Connect'
            )}
          </button>
        </form>

        <p className="text-center text-slate-500 text-xs mt-6">
          Connects via WebSocket to your OpenClaw gateway
        </p>
      </div>
    </div>
  );
}
