import { useState, useRef, useCallback, useEffect } from 'react';
import type { Message, GatewayFrame, ChatEvent, ConnectionState } from '../types';

let reqCounter = 0;
function nextId() {
  return `req-${++reqCounter}-${Date.now()}`;
}

function idempotencyKey() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function useGateway() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [connection, setConnection] = useState<ConnectionState>({ status: 'disconnected' });
  const [isStreaming, setIsStreaming] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const streamBufferRef = useRef<string>('');
  const currentRunIdRef = useRef<string | null>(null);
  const sessionKeyRef = useRef('agent:main:main');
  const gatewayUrlRef = useRef('');
  const tokenRef = useRef('');

  const sendFrame = useCallback((frame: GatewayFrame) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(frame));
    }
  }, []);

  const handleChatEvent = useCallback((event: ChatEvent) => {
    if (event.state === 'delta' && event.message?.content) {
      streamBufferRef.current += event.message.content;
      currentRunIdRef.current = event.runId;

      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last?.streaming) {
          return [
            ...prev.slice(0, -1),
            { ...last, content: streamBufferRef.current },
          ];
        }
        return [
          ...prev,
          {
            id: event.runId,
            role: 'assistant',
            content: streamBufferRef.current,
            timestamp: Date.now(),
            streaming: true,
          },
        ];
      });
    } else if (event.state === 'final') {
      const finalContent = event.message?.content || streamBufferRef.current;
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last?.streaming) {
          return [
            ...prev.slice(0, -1),
            { ...last, content: finalContent, streaming: false },
          ];
        }
        return prev;
      });
      streamBufferRef.current = '';
      currentRunIdRef.current = null;
      setIsStreaming(false);
    } else if (event.state === 'error') {
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last?.streaming) {
          return [
            ...prev.slice(0, -1),
            {
              ...last,
              content: event.errorMessage || 'An error occurred',
              streaming: false,
            },
          ];
        }
        return [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: 'system',
            content: event.errorMessage || 'An error occurred',
            timestamp: Date.now(),
          },
        ];
      });
      streamBufferRef.current = '';
      currentRunIdRef.current = null;
      setIsStreaming(false);
    } else if (event.state === 'aborted') {
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last?.streaming) {
          return [
            ...prev.slice(0, -1),
            { ...last, content: last.content + '\n\n[aborted]', streaming: false },
          ];
        }
        return prev;
      });
      streamBufferRef.current = '';
      currentRunIdRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  const handleMessage = useCallback((data: string) => {
    try {
      const frame: GatewayFrame = JSON.parse(data);

      if (frame.type === 'event' && frame.event === 'chat') {
        handleChatEvent(frame.payload as unknown as ChatEvent);
      }

      if (frame.type === 'res' && frame.ok && frame.id?.startsWith('history-')) {
        const history = frame.payload as { messages?: Array<{ role: string; content: string; timestamp?: number }> };
        if (history.messages?.length) {
          const loaded: Message[] = history.messages.map((m, i) => ({
            id: `hist-${i}`,
            role: m.role as Message['role'],
            content: m.content,
            timestamp: m.timestamp || Date.now(),
          }));
          setMessages(loaded);
        }
      }
    } catch {
      // ignore malformed frames
    }
  }, [handleChatEvent]);

  const connect = useCallback((gatewayUrl: string, token: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    gatewayUrlRef.current = gatewayUrl;
    tokenRef.current = token;
    setConnection({ status: 'connecting' });

    const wsUrl = gatewayUrl.replace(/^http/, 'ws');
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      sendFrame({
        type: 'req',
        id: nextId(),
        method: 'connect',
        params: {
          minProtocol: 3,
          maxProtocol: 3,
          client: {
            id: 'webchat-ui',
            version: '1.0.0',
            platform: 'web',
            mode: 'webchat',
          },
          role: 'operator',
          scopes: ['operator.read', 'operator.write'],
          auth: { token },
          locale: navigator.language || 'en-US',
        },
      });
    };

    ws.onmessage = (e) => {
      const data = typeof e.data === 'string' ? e.data : '';
      try {
        const frame: GatewayFrame = JSON.parse(data);

        // Handle connect response
        if (frame.type === 'res' && frame.ok !== undefined) {
          if (frame.ok) {
            setConnection({ status: 'connected' });
            // Load chat history
            sendFrame({
              type: 'req',
              id: `history-${nextId()}`,
              method: 'chat.history',
              params: {
                sessionKey: sessionKeyRef.current,
                limit: 100,
              },
            });
          } else {
            setConnection({
              status: 'error',
              error: (frame.payload as { message?: string })?.message || 'Connection rejected',
            });
            ws.close();
            return;
          }
        }

        handleMessage(data);
      } catch {
        // ignore
      }
    };

    ws.onerror = () => {
      setConnection({ status: 'error', error: 'WebSocket error' });
    };

    ws.onclose = (e) => {
      if (connection.status !== 'error') {
        setConnection({
          status: 'disconnected',
          error: e.code !== 1000 ? `Disconnected (code ${e.code})` : undefined,
        });
      }
    };
  }, [sendFrame, handleMessage, connection.status]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnection({ status: 'disconnected' });
    setMessages([]);
  }, []);

  const sendMessage = useCallback((text: string) => {
    if (!text.trim() || isStreaming) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text.trim(),
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, userMsg]);

    streamBufferRef.current = '';
    setIsStreaming(true);

    sendFrame({
      type: 'req',
      id: nextId(),
      method: 'chat.send',
      params: {
        sessionKey: sessionKeyRef.current,
        message: text.trim(),
        idempotencyKey: idempotencyKey(),
      },
    });
  }, [sendFrame, isStreaming]);

  const abortChat = useCallback(() => {
    sendFrame({
      type: 'req',
      id: nextId(),
      method: 'chat.abort',
      params: {
        sessionKey: sessionKeyRef.current,
        runId: currentRunIdRef.current || undefined,
      },
    });
  }, [sendFrame]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return {
    messages,
    connection,
    isStreaming,
    connect,
    disconnect,
    sendMessage,
    abortChat,
  };
}
