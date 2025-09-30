import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthGate } from '../features/auth/AuthGate'
import { LoginPage } from '../features/auth/LoginPage'
import { HomePage } from '../pages/HomePage'
import { CalendarPage } from '../pages/CalendarPage'
import { StreaksPage } from '../pages/StreaksPage'
import { AgentPage } from '../pages/AgentPage'
import { TodosPage } from '../pages/TodosPage'
import { IntegrationsPage } from '../pages/IntegrationsPage'
import { OAuthSuccessPage } from '../pages/OAuthSuccessPage'
import { OAuthErrorPage } from '../pages/OAuthErrorPage'
import { AppShell } from '../components/layout/AppShell'

function ProtectedRoutes() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/todos" element={<TodosPage />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/streaks" element={<StreaksPage />} />
        <Route path="/agent" element={<AgentPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/auth/*" element={<LoginPage />} />
      <Route path="/oauth/success" element={<OAuthSuccessPage />} />
      <Route path="/oauth/error" element={<OAuthErrorPage />} />
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