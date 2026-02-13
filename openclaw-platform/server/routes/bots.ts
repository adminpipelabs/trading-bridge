import { Router } from 'express';
import jwt from 'jsonwebtoken';
import crypto from 'crypto';
import { getDb } from '../db/schema.js';

const router = Router();
const JWT_SECRET = process.env.JWT_SECRET || 'bf-dev-secret-change-in-production';

function getUserId(req: any): string | null {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) return null;
  try {
    const payload = jwt.verify(authHeader.slice(7), JWT_SECRET) as { userId: string };
    return payload.userId;
  } catch {
    return null;
  }
}

// List all bots for user
router.get('/', (req, res) => {
  const userId = getUserId(req);
  if (!userId) return res.status(401).json({ message: 'Unauthorized' });

  const db = getDb();
  const bots = db.prepare('SELECT * FROM bots WHERE user_id = ? ORDER BY created_at DESC').all(userId);
  res.json({ bots });
});

// Get single bot
router.get('/:id', (req, res) => {
  const userId = getUserId(req);
  if (!userId) return res.status(401).json({ message: 'Unauthorized' });

  const db = getDb();
  const bot = db.prepare('SELECT * FROM bots WHERE id = ? AND user_id = ?').get(req.params.id, userId);
  if (!bot) return res.status(404).json({ message: 'Bot not found' });

  res.json({ bot });
});

// Create new bot
router.post('/', (req, res) => {
  const userId = getUserId(req);
  if (!userId) return res.status(401).json({ message: 'Unauthorized' });

  const { name, persona, model, channel, system_prompt } = req.body;
  if (!name?.trim()) return res.status(400).json({ message: 'Bot name is required' });

  const db = getDb();
  const id = crypto.randomUUID();

  db.prepare(`
    INSERT INTO bots (id, user_id, name, persona, model, channel, system_prompt, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'offline')
  `).run(
    id,
    userId,
    name.trim(),
    persona || 'friendly',
    model || 'anthropic',
    channel || '',
    system_prompt || 'You are a helpful personal AI assistant. Be concise, friendly, and proactive.',
  );

  const bot = db.prepare('SELECT * FROM bots WHERE id = ?').get(id);
  res.json({ bot });
});

// Update bot
router.put('/:id', (req, res) => {
  const userId = getUserId(req);
  if (!userId) return res.status(401).json({ message: 'Unauthorized' });

  const { name, persona, model, system_prompt, channel, status } = req.body;
  const db = getDb();

  const bot = db.prepare('SELECT * FROM bots WHERE id = ? AND user_id = ?').get(req.params.id, userId);
  if (!bot) return res.status(404).json({ message: 'Bot not found' });

  db.prepare(`
    UPDATE bots SET
      name = COALESCE(?, name),
      persona = COALESCE(?, persona),
      model = COALESCE(?, model),
      system_prompt = COALESCE(?, system_prompt),
      channel = COALESCE(?, channel),
      status = COALESCE(?, status)
    WHERE id = ? AND user_id = ?
  `).run(name, persona, model, system_prompt, channel, status, req.params.id, userId);

  const updated = db.prepare('SELECT * FROM bots WHERE id = ?').get(req.params.id);
  res.json({ bot: updated });
});

// Delete bot
router.delete('/:id', (req, res) => {
  const userId = getUserId(req);
  if (!userId) return res.status(401).json({ message: 'Unauthorized' });

  const db = getDb();
  const bot = db.prepare('SELECT * FROM bots WHERE id = ? AND user_id = ?').get(req.params.id, userId);
  if (!bot) return res.status(404).json({ message: 'Bot not found' });

  db.prepare('DELETE FROM bots WHERE id = ? AND user_id = ?').run(req.params.id, userId);
  res.json({ ok: true });
});

export default router;
