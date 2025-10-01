import { API_BASE_URL } from '../../config/api'
import { supabase } from '../supabase'

class ApiClient {
  private baseUrl: string
  private defaultTimeout: number = 10000 // 10 seconds default
  private quickTimeout: number = 5000   // 5 seconds for quick requests
  private longTimeout: number = 30000   // 30 seconds for agent requests

  // Circuit breaker state
  private circuitBreaker = {
    state: 'CLOSED' as 'CLOSED' | 'OPEN' | 'HALF_OPEN',
    failures: 0,
    lastFailureTime: 0,
  }
  private maxFailures = 3
  private resetTimeout = 30000 // 30 seconds

  constructor() {
    this.baseUrl = API_BASE_URL
  }

  private createTimeoutSignal(timeout: number): AbortSignal {
    const controller = new AbortController()
    setTimeout(() => controller.abort(), timeout)
    return controller.signal
  }

  private checkCircuitBreaker(): void {
    const now = Date.now()
    
    if (this.circuitBreaker.state === 'OPEN') {
      // Check if we should transition to half-open
      if (now - this.circuitBreaker.lastFailureTime > this.resetTimeout) {
        this.circuitBreaker.state = 'HALF_OPEN'

      } else {
        throw new Error('Service temporarily unavailable. Circuit breaker is OPEN.')
      }
    }
  }

  private recordSuccess(): void {
    if (this.circuitBreaker.failures > 0) {

      this.circuitBreaker.failures = 0
      this.circuitBreaker.state = 'CLOSED'
    }
  }

  private recordFailure(): void {
    this.circuitBreaker.failures++
    this.circuitBreaker.lastFailureTime = Date.now()
    
    if (this.circuitBreaker.failures >= this.maxFailures) {
      this.circuitBreaker.state = 'OPEN'
      console.error(`🚨 Circuit breaker OPEN after ${this.circuitBreaker.failures} failures`)
    } else {
      console.warn(`⚠️ Circuit breaker failure ${this.circuitBreaker.failures}/${this.maxFailures}`)
    }
  }

  private async getAuthToken(): Promise<string | null> {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      return session?.access_token || null
    } catch (error) {
      console.error('Error getting auth token:', error)
      return null
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeout?: number
  ): Promise<{ data: T | null; error: string | null }> {
    try {
      // Check circuit breaker before making request
      this.checkCircuitBreaker()
      
      const token = await this.getAuthToken()
      const url = `${this.baseUrl}${endpoint}`

      // Determine appropriate timeout
      const requestTimeout = timeout || this.getTimeoutForEndpoint(endpoint)
      const timeoutSignal = this.createTimeoutSignal(requestTimeout)

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
      }

      if (token) {
        headers.Authorization = `Bearer ${token}`
      }

      const response = await fetch(url, {
        ...options,
        headers,
        signal: timeoutSignal,
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication expired. Please log in again.')
        }
        if (response.status === 403) {
          throw new Error('Access denied. Please check your authentication.')
        }
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Record success for circuit breaker
      this.recordSuccess()
      
      return { data, error: null }
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error)
      
      // Record failure for circuit breaker (unless it's a circuit breaker error)
      if (!(error instanceof Error && error.message.includes('Circuit breaker is OPEN'))) {
        this.recordFailure()
      }
      
      // Handle specific timeout errors
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          return {
            data: null,
            error: 'Request timed out. The server may be unresponsive.'
          }
        }
        if (error.message.includes('fetch')) {
          return {
            data: null,
            error: 'Unable to connect to server. Please check your connection.'
          }
        }
        if (error.message.includes('Circuit breaker is OPEN')) {
          return {
            data: null,
            error: 'Service temporarily unavailable. Please try again later.'
          }
        }
      }
      
      return {
        data: null,
        error: error instanceof Error ? error.message : 'An unknown error occurred'
      }
    }
  }

  private getTimeoutForEndpoint(endpoint: string): number {
    // Unified agent requests need more time for processing
    if (endpoint.includes('/agents/')) {
      return this.longTimeout
    }
    // Health checks and quick operations
    if (endpoint.includes('/health')) {
      return this.quickTimeout
    }
    // Default timeout for other requests
    return this.defaultTimeout
  }

  async get<T>(endpoint: string): Promise<{ data: T | null; error: string | null }> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(
    endpoint: string,
    body?: any
  ): Promise<{ data: T | null; error: string | null }> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  async patch<T>(
    endpoint: string,
    body?: any
  ): Promise<{ data: T | null; error: string | null }> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<{ data: T | null; error: string | null }> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  async testConnection(): Promise<boolean> {
    try {
      const timeoutSignal = this.createTimeoutSignal(3000) // 3 second timeout for connection test
      const response = await fetch(`${this.baseUrl}/`, {
        method: 'GET',
        signal: timeoutSignal,
      })
      return response.ok
    } catch (error) {
      console.error('Connection test failed:', error)
      return false
    }
  }

  // Add method to set custom timeouts
  setTimeouts(options: {
    default?: number
    quick?: number
    long?: number
  }) {
    if (options.default) this.defaultTimeout = options.default
    if (options.quick) this.quickTimeout = options.quick
    if (options.long) this.longTimeout = options.long
  }

  // Get current timeout settings
  getTimeouts() {
    return {
      default: this.defaultTimeout,
      quick: this.quickTimeout,
      long: this.longTimeout
    }
  }
}

export const apiClient = new ApiClient()
