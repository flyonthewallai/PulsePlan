/**
 * Focus Session Service
 * Handles all focus session / Pomodoro tracking API calls
 */

import { supabase } from '../lib/supabase'
import { config } from '../lib/config'

const API_BASE_URL = config.api.baseUrl
const FOCUS_SESSIONS_ENDPOINT = `${API_BASE_URL}/api/v1/focus-sessions`

export interface FocusSession {
  id: string
  user_id: string
  start_time: string
  end_time?: string
  actual_start_time?: string
  actual_end_time?: string
  expected_duration: number
  duration_minutes?: number
  session_type: 'pomodoro' | 'deep_work' | 'study' | 'break'
  task_id?: string
  context?: string
  was_completed: boolean
  focus_score?: number
  interruption_count: number
  cycles_completed: number
  break_minutes: number
  session_notes?: string
  focus_quality?: Record<string, any>
  created_at: string
}

export interface FocusProfile {
  id: string
  user_id: string
  avg_focus_duration_minutes: number
  avg_break_duration_minutes: number
  avg_interruption_count: number
  avg_completion_ratio: number
  peak_focus_hours: number[]
  peak_focus_days: string[]
  avg_underestimation_pct: number
  total_sessions_count: number
  completed_sessions_count: number
  focus_by_hour: Record<number, number>
  performance_by_course?: Record<string, any>
  last_computed_at: string
  sessions_analyzed_count: number
}

export interface StartSessionRequest {
  expected_duration: number
  task_id?: string
  context?: string
  session_type?: 'pomodoro' | 'deep_work' | 'study' | 'break'
  auto_match_entity?: boolean
}

export interface MatchedEntity {
  type: 'task' | 'todo' | 'exam' | 'timeblock' | 'assignment'
  id: string | null
  entity: any
  confidence: number
  auto_created: boolean
  match_reason: string
}

export interface EntityMatchResult {
  success: boolean
  match: MatchedEntity
}

export interface EntitySuggestion {
  type: string
  id: string
  title: string
  subtitle?: string
  due_date?: string
}

export interface EndSessionRequest {
  was_completed?: boolean
  focus_score?: number
  interruption_count?: number
  session_notes?: string
}

/**
 * Get authentication headers for API calls
 */
async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session?.access_token) {
    throw new Error('Not authenticated')
  }
  
  return {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  }
}

/**
 * Start a new focus session with optional entity matching
 */
export async function startFocusSession(request: StartSessionRequest): Promise<{
  session: FocusSession
  matched_entity?: MatchedEntity
}> {
  try {
    const headers = await getAuthHeaders()
    
    const response = await fetch(`${FOCUS_SESSIONS_ENDPOINT}/start`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        expected_duration: request.expected_duration,
        task_id: request.task_id,
        context: request.context,
        session_type: request.session_type || 'pomodoro',
        auto_match_entity: request.auto_match_entity !== false, // Default true
      }),
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to start focus session')
    }
    
    const data = await response.json()
    return {
      session: data.session,
      matched_entity: data.matched_entity,
    }
  } catch (error) {
    console.error('Error starting focus session:', error)
    throw error
  }
}

/**
 * Preview entity matching without starting a session
 */
export async function matchEntity(
  input_text: string,
  duration_minutes?: number
): Promise<MatchedEntity | null> {
  try {
    const headers = await getAuthHeaders()
    
    const response = await fetch(`${API_BASE_URL}/api/v1/entity-matching/match`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ input_text, duration_minutes }),
    })
    
    if (!response.ok) {
      throw new Error('Failed to match entity')
    }
    
    const data: EntityMatchResult = await response.json()
    return data.match
  } catch (error) {
    console.error('Error matching entity:', error)
    return null
  }
}

/**
 * Get entity suggestions for autocomplete
 */
export async function getEntitySuggestions(
  query?: string,
  limit = 10
): Promise<EntitySuggestion[]> {
  try {
    const headers = await getAuthHeaders()
    
    const queryParams = new URLSearchParams()
    if (query) queryParams.set('query', query)
    queryParams.set('limit', limit.toString())
    
    const response = await fetch(
      `${API_BASE_URL}/api/v1/entity-matching/suggestions?${queryParams.toString()}`,
      {
        method: 'GET',
        headers,
      }
    )
    
    if (!response.ok) {
      throw new Error('Failed to get suggestions')
    }
    
    const data = await response.json()
    return data.suggestions || []
  } catch (error) {
    console.error('Error getting suggestions:', error)
    return []
  }
}

/**
 * End an active focus session
 */
export async function endFocusSession(
  sessionId: string,
  request: EndSessionRequest
): Promise<FocusSession> {
  try {
    const headers = await getAuthHeaders()
    
    const response = await fetch(`${FOCUS_SESSIONS_ENDPOINT}/${sessionId}/end`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        was_completed: request.was_completed ?? true,
        focus_score: request.focus_score,
        interruption_count: request.interruption_count ?? 0,
        session_notes: request.session_notes,
      }),
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to end focus session')
    }
    
    const data = await response.json()
    return data.session
  } catch (error) {
    console.error('Error ending focus session:', error)
    throw error
  }
}

/**
 * Get currently active session
 */
export async function getActiveSession(): Promise<FocusSession | null> {
  try {
    const headers = await getAuthHeaders()
    
    const response = await fetch(`${FOCUS_SESSIONS_ENDPOINT}/active`, {
      method: 'GET',
      headers,
    })
    
    if (!response.ok) {
      throw new Error('Failed to get active session')
    }
    
    const data = await response.json()
    return data.active_session
  } catch (error) {
    console.error('Error getting active session:', error)
    return null
  }
}

/**
 * Get session history
 */
export async function getSessionHistory(params?: {
  limit?: number
  offset?: number
  start_date?: string
  end_date?: string
  task_id?: string
}): Promise<FocusSession[]> {
  try {
    const headers = await getAuthHeaders()
    
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.set('limit', params.limit.toString())
    if (params?.offset) queryParams.set('offset', params.offset.toString())
    if (params?.start_date) queryParams.set('start_date', params.start_date)
    if (params?.end_date) queryParams.set('end_date', params.end_date)
    if (params?.task_id) queryParams.set('task_id', params.task_id)
    
    const url = `${FOCUS_SESSIONS_ENDPOINT}/history?${queryParams.toString()}`
    
    const response = await fetch(url, {
      method: 'GET',
      headers,
    })
    
    if (!response.ok) {
      throw new Error('Failed to get session history')
    }
    
    const data = await response.json()
    return data.sessions || []
  } catch (error) {
    console.error('Error getting session history:', error)
    return []
  }
}

/**
 * Get user's focus profile (analytics)
 */
export async function getFocusProfile(recompute = false): Promise<FocusProfile | null> {
  try {
    const headers = await getAuthHeaders()
    
    const queryParams = new URLSearchParams()
    if (recompute) queryParams.set('recompute', 'true')
    
    const url = `${FOCUS_SESSIONS_ENDPOINT}/profile?${queryParams.toString()}`
    
    const response = await fetch(url, {
      method: 'GET',
      headers,
    })
    
    if (!response.ok) {
      throw new Error('Failed to get focus profile')
    }
    
    const data = await response.json()
    return data.profile
  } catch (error) {
    console.error('Error getting focus profile:', error)
    return null
  }
}

/**
 * Get insights for a specific session
 */
export async function getSessionInsights(sessionId: string): Promise<any> {
  try {
    const headers = await getAuthHeaders()
    
    const response = await fetch(`${FOCUS_SESSIONS_ENDPOINT}/${sessionId}/insights`, {
      method: 'GET',
      headers,
    })
    
    if (!response.ok) {
      throw new Error('Failed to get session insights')
    }
    
    return await response.json()
  } catch (error) {
    console.error('Error getting session insights:', error)
    return { insights: [] }
  }
}

/**
 * Delete a focus session
 */
export async function deleteSession(sessionId: string): Promise<boolean> {
  try {
    const headers = await getAuthHeaders()
    
    const response = await fetch(`${FOCUS_SESSIONS_ENDPOINT}/${sessionId}`, {
      method: 'DELETE',
      headers,
    })
    
    if (!response.ok) {
      throw new Error('Failed to delete session')
    }
    
    return true
  } catch (error) {
    console.error('Error deleting session:', error)
    return false
  }
}


