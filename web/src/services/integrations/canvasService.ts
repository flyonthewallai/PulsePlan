import { API_BASE_URL } from '@/config/api'
import { supabase } from '@/lib/supabase'

export interface CanvasIntegrationStatus {
  connected: boolean
  lastSync: string | null
  assignmentsSynced?: number
  totalCanvasTasks: number
  extensionVersion?: string | null
  isSyncing?: boolean
  syncProgress?: {
    coursesProcessed: number
    totalCourses: number
    assignmentsSynced: number
    status: 'starting' | 'in_progress' | 'completed' | 'error'
    message?: string
  }
}

class CanvasService {
  private apiUrl = API_BASE_URL

  private async getAuthHeaders() {
    const { data: { session } } = await supabase.auth.getSession()
    const token = session?.access_token
    if (!token) throw new Error('Not authenticated')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    }
  }

  async getIntegrationStatus(): Promise<CanvasIntegrationStatus> {
    const headers = await this.getAuthHeaders()
    const res = await fetch(`${this.apiUrl}/api/v1/integrations/canvas/status`, { headers })
    if (!res.ok) {
      throw new Error(`Failed to fetch Canvas status: ${res.status}`)
    }
    const raw = await res.json()
    // Map backend snake_case to frontend camelCase
    return {
      connected: Boolean(raw.connected),
      lastSync: raw.last_sync ?? null,
      assignmentsSynced: raw.assignments_count ?? raw.total_assignments ?? undefined,
      totalCanvasTasks: raw.assignments_count ?? raw.total_canvas_tasks ?? 0,
      extensionVersion: raw.extension_version ?? null,
      isSyncing: raw.is_syncing ?? false,
      syncProgress: raw.sync_progress
        ? {
            coursesProcessed: raw.sync_progress.courses_processed ?? 0,
            totalCourses: raw.sync_progress.total_courses ?? 0,
            assignmentsSynced: raw.sync_progress.assignments_synced ?? 0,
            status: raw.sync_progress.status ?? 'in_progress',
            message: raw.sync_progress.message,
          }
        : undefined,
    }
  }

  async connectWithAPIKey(canvasUrl: string, apiToken: string): Promise<{ success: boolean } & Record<string, any>> {
    const headers = await this.getAuthHeaders()
    const res = await fetch(`${this.apiUrl}/api/v1/integrations/canvas/connect`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ canvas_url: canvasUrl, api_token: apiToken })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to connect Canvas')
    }
    return data
  }

  async disconnect(): Promise<{ success: boolean } & Record<string, any>> {
    const headers = await this.getAuthHeaders()
    const res = await fetch(`${this.apiUrl}/api/v1/integrations/canvas/disconnect`, {
      method: 'DELETE',
      headers
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to disconnect Canvas')
    }
    return data
  }

  async triggerSync(syncType: 'full' | 'delta' = 'delta'): Promise<{ success: boolean; sync_id: string } & Record<string, any>> {
    const headers = await this.getAuthHeaders()
    const res = await fetch(`${this.apiUrl}/api/v1/integrations/canvas/sync`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ sync_type: syncType, force_restart: false })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to trigger Canvas sync')
    }
    return data
  }
}

export const canvasService = new CanvasService()

export function formatLastSync(lastSync: string | null): string {
  if (!lastSync) return 'Never'
  const date = new Date(lastSync)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
  return date.toLocaleDateString()
}


