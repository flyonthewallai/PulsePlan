import { API_BASE_URL } from '@/config/api'
import { supabase } from '@/lib/supabase'

interface ApiServiceOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  body?: Record<string, unknown> | unknown[]
  headers?: Record<string, string>
}

class ApiService {
  private baseUrl = API_BASE_URL

  private async getAuthHeaders() {
    const { data: { session } } = await supabase.auth.getSession()
    const token = session?.access_token
    if (!token) throw new Error('Not authenticated')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    }
  }

  private async request(endpoint: string, options: ApiServiceOptions = {}) {
    try {
      const { method = 'GET', body, headers: customHeaders } = options
      const authHeaders = await this.getAuthHeaders()
      
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method,
        headers: {
          ...authHeaders,
          ...customHeaders,
        },
        body: body ? JSON.stringify(body) : undefined,
      })

      // Handle various response types
      if (!response.ok) {
        const errorText = await response.text()
        let errorData
        try {
          errorData = JSON.parse(errorText)
        } catch {
          errorData = { detail: errorText || response.statusText }
        }
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`)
      }

      // For 204 No Content responses, return null
      if (response.status === 204) {
        return null
      }

      // Try to parse JSON, but handle non-JSON responses
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }

      return await response.text()
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  async get<T = unknown>(endpoint: string, options?: ApiServiceOptions): Promise<T> {
    return this.request(endpoint, { ...options, method: 'GET' }) as Promise<T>
  }

  async post<T = unknown>(endpoint: string, body?: Record<string, unknown> | unknown[], options?: ApiServiceOptions): Promise<T> {
    return this.request(endpoint, { ...options, method: 'POST', body }) as Promise<T>
  }

  async put<T = unknown>(endpoint: string, body?: Record<string, unknown> | unknown[], options?: ApiServiceOptions): Promise<T> {
    return this.request(endpoint, { ...options, method: 'PUT', body }) as Promise<T>
  }

  async patch<T = unknown>(endpoint: string, body?: Record<string, unknown> | unknown[], options?: ApiServiceOptions): Promise<T> {
    return this.request(endpoint, { ...options, method: 'PATCH', body }) as Promise<T>
  }

  async delete<T = unknown>(endpoint: string, options?: ApiServiceOptions): Promise<T> {
    return this.request(endpoint, { ...options, method: 'DELETE' }) as Promise<T>
  }

  // AI-driven event creation
  async createEventWithAI(prompt: string, timeSlot: { start: string; end: string }): Promise<{ event: unknown }> {
    return this.post('/api/v1/agents/event', {
      prompt,
      start_date: timeSlot.start,
      end_date: timeSlot.end,
    })
  }
}

export const apiService = new ApiService()





