import { config } from '@/lib/config'

const API_BASE_URL = config.api.baseUrl

export interface PomodoroSettings {
  focus_minutes: number
  break_minutes: number
  long_break_minutes: number
  cycles_per_session: number
  auto_start_breaks: boolean
  auto_start_next_session: boolean
  play_sound_on_complete: boolean
  desktop_notifications: boolean
}

export async function getPomodoroSettings(): Promise<PomodoroSettings> {
  const res = await fetch(`${API_BASE_URL}/api/v1/pomodoro/settings`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to fetch settings')
  return await res.json()
}

export async function putPomodoroSettings(settings: PomodoroSettings): Promise<PomodoroSettings> {
  const res = await fetch(`${API_BASE_URL}/api/v1/pomodoro/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(settings)
  })
  if (!res.ok) throw new Error('Failed to save settings')
  return await res.json()
}








