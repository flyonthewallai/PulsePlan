import { config } from '@/lib/config'

const API_BASE_URL = config.api.baseUrl

export type PhaseType = 'focus' | 'break' | 'long_break'

export async function startPhase(params: { session_id: string; phase_type: PhaseType; expected_duration_minutes?: number }) {
  const res = await fetch(`${API_BASE_URL}/api/v1/pomodoro/phases/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(params)
  })
  if (!res.ok) throw new Error('Failed to start phase')
  return await res.json()
}

export async function endPhase(params: { phase_id: string; interrupted?: boolean; ended_at_iso?: string }) {
  const res = await fetch(`${API_BASE_URL}/api/v1/pomodoro/phases/end`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(params)
  })
  if (!res.ok) throw new Error('Failed to end phase')
  return await res.json()
}








