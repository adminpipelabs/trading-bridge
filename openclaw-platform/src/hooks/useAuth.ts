import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import type { User, AuthState } from '../types';
import { api } from '../api/client';

const AuthContext = createContext<{
  auth: AuthState;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
} | null>(null);

export const AuthProvider = AuthContext.Provider;

export function useAuthProvider() {
  const [auth, setAuth] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('bf-token'),
    loading: true,
  });

  // Load user on mount if token exists
  useEffect(() => {
    const token = localStorage.getItem('bf-token');
    const user = localStorage.getItem('bf-user');
    if (token && user) {
      try {
        setAuth({ user: JSON.parse(user), token, loading: false });
      } catch {
        localStorage.removeItem('bf-token');
        localStorage.removeItem('bf-user');
        setAuth({ user: null, token: null, loading: false });
      }
    } else {
      setAuth({ user: null, token: null, loading: false });
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.post('/api/auth/login', { email, password });
    const { user, token } = res as { user: User; token: string };
    localStorage.setItem('bf-token', token);
    localStorage.setItem('bf-user', JSON.stringify(user));
    setAuth({ user, token, loading: false });
  }, []);

  const signup = useCallback(async (name: string, email: string, password: string) => {
    const res = await api.post('/api/auth/signup', { name, email, password });
    const { user, token } = res as { user: User; token: string };
    localStorage.setItem('bf-token', token);
    localStorage.setItem('bf-user', JSON.stringify(user));
    setAuth({ user, token, loading: false });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('bf-token');
    localStorage.removeItem('bf-user');
    setAuth({ user: null, token: null, loading: false });
  }, []);

  return { auth, login, signup, logout };
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
