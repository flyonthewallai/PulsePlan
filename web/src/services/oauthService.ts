import { supabase } from '../lib/supabase'
import { API_BASE_URL } from '../config/api'

export interface OAuthConnection {
  provider: 'google' | 'microsoft'
  connected: boolean
  user_email?: string
  expires_at?: string
  last_refreshed?: string
  scopes?: string[]
}

export interface OAuthInitiateResponse {
  authorization_url: string
  state: string
}

export type OAuthProvider = 'google' | 'microsoft'
export type OAuthService = 'calendar' | 'gmail' | 'contacts' | 'outlook'

class OAuthServiceClass {
  private apiUrl = API_BASE_URL

  private async getAuthenticatedUser() {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) {
      throw new Error('User not authenticated')
    }
    return user
  }

  private async getAuthHeaders() {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) {
      throw new Error('No valid session')
    }
    return {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    }
  }

  async initiateOAuth(provider: OAuthProvider, service: OAuthService = 'calendar'): Promise<OAuthInitiateResponse> {
    try {
      const user = await this.getAuthenticatedUser()

      const response = await fetch(`${this.apiUrl}/api/v1/oauth/${provider}/authorize?userId=${user.id}&service=${service}`)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to initiate ${provider} OAuth`)
      }

      return await response.json()
    } catch (error) {
      console.error(`Error initiating ${provider} OAuth:`, error)
      throw error
    }
  }

  async getOAuthConnections(): Promise<OAuthConnection[]> {
    try {
      const headers = await this.getAuthHeaders()

      const response = await fetch(`${this.apiUrl}/api/v1/auth/oauth/connections`, {
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to get OAuth connections')
      }

      return await response.json()
    } catch (error) {
      console.error('Error getting OAuth connections:', error)
      throw error
    }
  }

  async disconnectOAuth(provider: OAuthProvider): Promise<void> {
    try {
      const headers = await this.getAuthHeaders()

      const response = await fetch(`${this.apiUrl}/api/v1/auth/oauth/connections/${provider}`, {
        method: 'DELETE',
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to disconnect ${provider}`)
      }
    } catch (error) {
      console.error(`Error disconnecting ${provider}:`, error)
      throw error
    }
  }

  openOAuthWindow(authUrl: string): Promise<{ success: boolean; provider: string; error?: string }> {
    return new Promise((resolve) => {
      const popup = window.open(
        authUrl,
        'oauth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
      )

      if (!popup) {
        resolve({ success: false, provider: '', error: 'Popup blocked' })
        return
      }

      // Listen for the OAuth callback
      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed)
          resolve({ success: false, provider: '', error: 'Window closed by user' })
        }
      }, 1000)

      // Listen for messages from the OAuth callback
      const messageListener = (event: MessageEvent) => {
        // Verify origin for security
        if (event.origin !== window.location.origin) {
          return
        }

        if (event.data.type === 'oauth-success' || event.data.type === 'oauth-error') {
          clearInterval(checkClosed)
          popup.close()
          window.removeEventListener('message', messageListener)

          if (event.data.type === 'oauth-success') {
            resolve({
              success: true,
              provider: event.data.provider,
              error: undefined
            })
          } else {
            resolve({
              success: false,
              provider: event.data.provider || '',
              error: event.data.error || 'OAuth failed'
            })
          }
        }
      }

      window.addEventListener('message', messageListener)
    })
  }

  async connectProvider(provider: OAuthProvider, service: OAuthService = 'calendar'): Promise<{ success: boolean; error?: string }> {
    try {
      // Step 1: Get authorization URL
      const { authorization_url } = await this.initiateOAuth(provider, service)

      // Step 2: Open OAuth window and wait for result
      const result = await this.openOAuthWindow(authorization_url)

      if (!result.success) {
        return { success: false, error: result.error }
      }

      return { success: true }
    } catch (error) {
      console.error(`Error connecting ${provider}:`, error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }
}

const oauthServiceInstance = new OAuthServiceClass()

export { oauthServiceInstance as oauthService }