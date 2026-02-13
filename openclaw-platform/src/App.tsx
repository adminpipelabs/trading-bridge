import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthProvider, AuthProvider } from './hooks/useAuth';
import { useBotsProvider, BotsProvider } from './hooks/useBots';
import { AppShell } from './components/layout/AppShell';
import Landing from './routes/Landing';
import Login from './routes/Login';
import Signup from './routes/Signup';
import Onboarding from './routes/Onboarding';
import Dashboard from './routes/Dashboard';
import Chat from './routes/Chat';
import Integrations from './routes/Integrations';
import Analytics from './routes/Analytics';
import BotSettings from './routes/BotSettings';
import Activate from './routes/Activate';

/**
 * Access control:
 * - Has token → full access (authenticated user)
 * - Has draft bots but no token → sandbox mode (can see dashboard, settings, etc. but must activate to go live)
 * - Neither → redirect to landing/login
 */
function SmartRoute({ children }: { children: React.ReactNode }) {
  const hasToken = !!localStorage.getItem('bf-token');
  const hasDrafts = (JSON.parse(localStorage.getItem('bf-draft-bots') || '[]')).length > 0;

  if (!hasToken && !hasDrafts) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function AppContent() {
  const botsCtx = useBotsProvider();

  return (
    <BotsProvider value={botsCtx}>
      <AppShell />
    </BotsProvider>
  );
}

function AppRoutes() {
  const authCtx = useAuthProvider();

  return (
    <AuthProvider value={authCtx}>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/onboarding" element={<Onboarding />} />

        {/* Sandbox + authenticated routes */}
        <Route
          element={
            <SmartRoute>
              <AppContent />
            </SmartRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/integrations" element={<Integrations />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<BotSettings />} />
          <Route path="/activate" element={<Activate />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
