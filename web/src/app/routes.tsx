import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthGate } from '../features/auth/AuthGate'
import { AuthPage } from '../pages/AuthPage'
import { HomePage } from '../pages/HomePage'
import { CalendarPage } from '../pages/CalendarPage'
import { StreaksPage } from '../pages/StreaksPage'
import { AgentPage } from '../pages/AgentPage'
import { ChatPage } from '../pages/ChatPage'
import { TaskboardPage } from '../pages/TaskboardPage'
import { IntegrationsPage } from '../pages/IntegrationsPage'
import { OAuthSuccessPage } from '../pages/OAuthSuccessPage'
import { OAuthErrorPage } from '../pages/OAuthErrorPage'
import { AuthCallbackPage } from '../pages/AuthCallbackPage'
import { PomodoroPage } from '../pages/PomodoroPage'
import { PricingPage } from '../pages/PricingPage'
import AdminNLUPage from '../pages/AdminNLUPage'
import { AppShell } from '../components/layout/AppShell'

function ProtectedRoutes() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/taskboard" element={<TaskboardPage />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/streaks" element={<StreaksPage />} />
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