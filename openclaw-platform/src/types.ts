// Auth
export interface User {
  id: string;
  email: string;
  name: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
}

// Bot
export interface Bot {
  id: string;
  name: string;
  persona: string;
  model: string;
  status: 'online' | 'offline' | 'starting';
  createdAt: string;
  channels: string[];
  messagesTotal: number;
  messagestoday: number;
  avgResponseTime: number;
  uptime: number;
}

// Integrations
export interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'channel' | 'skill' | 'tool';
  status: 'connected' | 'available' | 'coming_soon';
  popular?: boolean;
  setupUrl?: string;
}

// Analytics
export interface DailyStat {
  date: string;
  messages: number;
  responseTime: number;
}

export interface ChannelStat {
  channel: string;
  messages: number;
  percentage: number;
}

// Opportunity suggestions
export interface Opportunity {
  id: string;
  type: 'integration' | 'skill' | 'optimization';
  title: string;
  description: string;
  actionLabel: string;
  actionUrl: string;
  priority: 'high' | 'medium' | 'low';
}

// Chat (reused from previous build)
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  streaming?: boolean;
}

export interface GatewayFrame {
  type: 'req' | 'res' | 'event';
  id?: string;
  method?: string;
  params?: Record<string, unknown>;
  ok?: boolean;
  payload?: Record<string, unknown>;
  event?: string;
}

export interface ChatEvent {
  runId: string;
  sessionKey: string;
  seq: number;
  state: 'delta' | 'final' | 'aborted' | 'error';
  message?: {
    content?: string;
    role?: string;
  };
  errorMessage?: string;
}

export interface ConnectionState {
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  error?: string;
}
