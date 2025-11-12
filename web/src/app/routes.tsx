import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthGate } from '../features/auth/AuthGate'
import { AuthPage, AuthCallbackPage, OAuthSuccessPage, OAuthErrorPage } from '../pages/auth'
import { HomePage } from '../pages/home'
import { CalendarPage } from '../pages/calendar'
import { AgentPage } from '../pages/chat'
import { ChatPage } from '../pages/chat'
import { TaskboardPage } from '../pages/tasks'
import { IntegrationsPage } from '../pages/integrations'
import { PomodoroPage } from '../pages/pomodoro'
import { PricingPage } from '../pages/pricing'
import { AdminNLUPage } from '../pages/admin'
import { AppShell } from '../components/layout/AppShell'

function ProtectedRoutes() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/taskboard" element={<TaskboardPage />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/agent" element={<AgentPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/pomodoro" element={<PomodoroPage />} />
        <Route path="/admin/nlu" element={<AdminNLUPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/auth/*" element={<AuthPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route path="/oauth/success" element={<OAuthSuccessPage />} />
      <Route path="/oauth/error" element={<OAuthErrorPage />} />
      <Route
        path="/pricing"
        element={
          <AuthGate fallback={<Navigate to="/auth" replace />}>
            <PricingPage />
          </AuthGate>
        }
      />
      <Route
        path="/*"
        element={
          <AuthGate fallback={<Navigate to="/auth" replace />}>
            <ProtectedRoutes />
          </AuthGate>
        }
      />
    </Routes>
  )
}