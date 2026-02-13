import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { api } from '../api/client';

export interface BotData {
  id: string;
  name: string;
  persona: string;
  model: string;
  channel: string;
  system_prompt: string;
  status: string; // 'draft' | 'offline' | 'online' | 'starting'
  created_at: string;
}

interface BotsState {
  bots: BotData[];
  selectedBot: BotData | null;
  loading: boolean;
  isAuthenticated: boolean;
  selectBot: (id: string) => void;
  refresh: () => Promise<void>;
  createBot: (data: { name: string; persona: string; model: string; channel: string }) => Promise<BotData>;
  updateBot: (id: string, data: Partial<BotData>) => Promise<void>;
  deleteBot: (id: string) => Promise<void>;
  updateDraftBot: (id: string, data: Partial<BotData>) => void;
}

const BotsContext = createContext<BotsState | null>(null);

export const BotsProvider = BotsContext.Provider;

// Read draft bots from localStorage
function getDraftBots(): BotData[] {
  try {
    const raw = localStorage.getItem('bf-draft-bots');
    if (!raw) return [];
    return JSON.parse(raw).map((d: any) => ({
      ...d,
      system_prompt: d.system_prompt || 'You are a helpful personal AI assistant.',
      status: 'draft',
    }));
  } catch {
    return [];
  }
}

function saveDraftBots(bots: BotData[]) {
  localStorage.setItem('bf-draft-bots', JSON.stringify(bots));
}

export function useBotsProvider() {
  const [bots, setBots] = useState<BotData[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<string | null>(
    () => localStorage.getItem('bf-selected-bot')
  );
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!localStorage.getItem('bf-token');

  const refresh = useCallback(async () => {
    try {
      if (isAuthenticated) {
        // Fetch real bots from API
        const res = await api.get('/api/bots') as { bots: BotData[] };
        const serverBots = res.bots || [];

        // Also include any remaining draft bots (not yet claimed)
        const drafts = getDraftBots();
        const all = [...serverBots, ...drafts];
        setBots(all);

        if (all.length && !selectedBotId) {
          setSelectedBotId(all[0].id);
          localStorage.setItem('bf-selected-bot', all[0].id);
        }
      } else {
        // Not logged in — show draft bots only
        const drafts = getDraftBots();
        setBots(drafts);

        if (drafts.length && !selectedBotId) {
          setSelectedBotId(drafts[0].id);
          localStorage.setItem('bf-selected-bot', drafts[0].id);
        }
      }
    } catch {
      // Fall back to drafts if API fails
      const drafts = getDraftBots();
      setBots(drafts);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, selectedBotId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const selectBot = useCallback((id: string) => {
    setSelectedBotId(id);
    localStorage.setItem('bf-selected-bot', id);
  }, []);

  const selectedBot = bots.find((b) => b.id === selectedBotId) || bots[0] || null;

  const createBot = useCallback(async (data: { name: string; persona: string; model: string; channel: string }) => {
    if (isAuthenticated) {
      const res = await api.post('/api/bots', data) as { bot: BotData };
      setBots((prev) => [res.bot, ...prev]);
      setSelectedBotId(res.bot.id);
      localStorage.setItem('bf-selected-bot', res.bot.id);
      return res.bot;
    } else {
      // Create as draft
      const draft: BotData = {
        id: `draft-${Date.now()}`,
        name: data.name,
        persona: data.persona,
        model: data.model,
        channel: data.channel,
        system_prompt: 'You are a helpful personal AI assistant.',
        status: 'draft',
        created_at: new Date().toISOString(),
      };
      const drafts = getDraftBots();
      drafts.unshift(draft);
      saveDraftBots(drafts);
      setBots((prev) => [draft, ...prev]);
      setSelectedBotId(draft.id);
      localStorage.setItem('bf-selected-bot', draft.id);
      return draft;
    }
  }, [isAuthenticated]);

  const updateBot = useCallback(async (id: string, data: Partial<BotData>) => {
    if (id.startsWith('draft-')) {
      // Update draft in localStorage
      const drafts = getDraftBots();
      const updated = drafts.map((b) => b.id === id ? { ...b, ...data } : b);
      saveDraftBots(updated);
      setBots((prev) => prev.map((b) => b.id === id ? { ...b, ...data } : b));
    } else {
      const res = await api.put(`/api/bots/${id}`, data) as { bot: BotData };
      setBots((prev) => prev.map((b) => (b.id === id ? res.bot : b)));
    }
  }, []);

  const updateDraftBot = useCallback((id: string, data: Partial<BotData>) => {
    const drafts = getDraftBots();
    const updated = drafts.map((b) => b.id === id ? { ...b, ...data } : b);
    saveDraftBots(updated);
    setBots((prev) => prev.map((b) => b.id === id ? { ...b, ...data } : b));
  }, []);

  const deleteBot = useCallback(async (id: string) => {
    if (id.startsWith('draft-')) {
      const drafts = getDraftBots().filter((b) => b.id !== id);
      saveDraftBots(drafts);
      setBots((prev) => {
        const remaining = prev.filter((b) => b.id !== id);
        if (selectedBotId === id && remaining.length > 0) {
          setSelectedBotId(remaining[0].id);
          localStorage.setItem('bf-selected-bot', remaining[0].id);
        }
        return remaining;
      });
    } else {
      await api.delete(`/api/bots/${id}`);
      setBots((prev) => {
        const remaining = prev.filter((b) => b.id !== id);
        if (selectedBotId === id && remaining.length > 0) {
          setSelectedBotId(remaining[0].id);
          localStorage.setItem('bf-selected-bot', remaining[0].id);
        }
        return remaining;
      });
    }
  }, [selectedBotId]);

  return { bots, selectedBot, loading, isAuthenticated, selectBot, refresh, createBot, updateBot, updateDraftBot, deleteBot };
}

export function useBots() {
  const ctx = useContext(BotsContext);
  if (!ctx) throw new Error('useBots must be used within BotsProvider');
  return ctx;
}
