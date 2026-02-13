import { useState, useEffect } from 'react';
import { Save, Trash2 } from 'lucide-react';
import { useBots } from '../hooks/useBots';
import { useNavigate } from 'react-router-dom';

export default function BotSettings() {
  const { selectedBot, updateBot, deleteBot } = useBots();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [persona, setPersona] = useState('friendly');
  const [model, setModel] = useState('anthropic');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (selectedBot) {
      setName(selectedBot.name);
      setPersona(selectedBot.persona);
      setModel(selectedBot.model);
      setSystemPrompt(selectedBot.system_prompt || '');
    }
  }, [selectedBot]);

  if (!selectedBot) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        Select a bot from the dashboard first
      </div>
    );
  }

  const handleSave = async () => {
    await updateBot(selectedBot.id, { name, persona, model, system_prompt: systemPrompt });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleDelete = async () => {
    if (confirm(`Delete "${selectedBot.name}"? This cannot be undone.`)) {
      await deleteBot(selectedBot.id);
      navigate('/dashboard');
    }
  };

  return (
    <div className="px-4 sm:px-8 py-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Bot Settings</h1>
          <p className="text-sm text-slate-400 mt-1">Configure {selectedBot.name}</p>
        </div>
        <button
          onClick={handleSave}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <Save className="w-4 h-4" />
          {saved ? 'Saved!' : 'Save'}
        </button>
      </div>

      <div className="space-y-6">
        {/* General */}
        <div className="bg-slate-800/40 border border-slate-700/40 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-4">General</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Bot Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Personality</label>
              <select
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
              >
                <option value="friendly">Friendly</option>
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
              </select>
            </div>
          </div>
        </div>

        {/* Model */}
        <div className="bg-slate-800/40 border border-slate-700/40 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-4">Model</h3>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
          >
            <option value="anthropic">Anthropic (Claude)</option>
            <option value="openai">OpenAI (GPT)</option>
            <option value="local">Local / OpenRouter</option>
          </select>
        </div>

        {/* System prompt */}
        <div className="bg-slate-800/40 border border-slate-700/40 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-4">System Prompt</h3>
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={5}
            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all resize-none text-sm leading-relaxed"
          />
          <p className="text-xs text-slate-500 mt-2">
            Base instruction for this bot. Defines how it behaves and responds.
          </p>
        </div>

        {/* Danger zone */}
        <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-6">
          <h3 className="text-red-400 font-semibold mb-2">Danger Zone</h3>
          <p className="text-sm text-slate-400 mb-4">
            Permanently delete this bot and all its data.
          </p>
          <button
            onClick={handleDelete}
            className="inline-flex items-center gap-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-sm font-medium rounded-lg border border-red-500/20 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete Bot
          </button>
        </div>
      </div>
    </div>
  );
}
