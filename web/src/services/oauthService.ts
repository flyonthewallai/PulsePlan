import { supabase } from '../lib/supabase'
import { API_BASE_URL } from '../config/api'

export interface OAuthConnection {
  provider: 'google' | 'microsoft'
  service: string  // calendar, gmail, contacts, outlook
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

type ConnectOptions = {
  mode?: 'popup' | 'redirect'
}

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

      const response = await fetch(`${this.apiUrl}/api/v1/auth/oauth/${provider}/authorize?userId=${user.id}&service=${service}`)

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

  async disconnectOAuth(provider: OAuthProvider, service: OAuthService): Promise<void> {
    try {
      const headers = await this.getAuthHeaders()

      const response = await fetch(`${this.apiUrl}/api/v1/auth/oauth/connections/${provider}/${service}`, {
        method: 'DELETE',
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to disconnect ${provider}/${service}`)
      }
    } catch (error) {
      console.error(`Error disconnecting ${provider}/${service}:`, error)
      throw error
    }
  }

  openOAuthWindow(
    authUrl: string,
    opts?: { onPopup?: (popup: Window) => void }
  ): Promise<{ success: boolean; provider: string; error?: string }> {
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

      // Expose popup reference to caller for optional external control
      try {
        opts?.onPopup?.(popup)
      } catch {}

      let resolved = false

      const cleanup = () => {
        if (resolved) return
        resolved = true
        clearTimeout(timeout)
        clearInterval(closedInterval)
        window.removeEventListener('message', messageListener)
      }

      // Timeout to prevent hanging if popup is closed without message
      const timeout = setTimeout(() => {
        cleanup()
        resolve({ success: false, provider: '', error: 'OAuth timed out' })
      }, 120000) // 2 minute timeout

      // Detect manual popup close to fail fast if no message is received
      const closedInterval = setInterval(() => {
        try {
          if (popup.closed) {
            cleanup()
            resolve({ success: false, provider: '', error: 'Window closed' })
          }
        } catch {
          // Ignore cross-origin access errors while popup is on provider domain
        }
      }, 500)

      // Listen for messages from the OAuth callback
      const messageListener = (event: MessageEvent) => {
        // Validate by source window primarily to support different callback origins
        if (event.source !== popup) {
          return
        }

        if (event.data && (event.data.type === 'oauth-success' || event.data.type === 'oauth-error')) {
          cleanup()

          // Try to close popup, but don't fail if COOP blocks it
          try {
            popup.close()
          } catch (e) {
            console.warn('Could not close popup (likely due to COOP policy):', e)
          }

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

  async connectProvider(
    provider: OAuthProvider,
    service: OAuthService = 'calendar',
    options?: ConnectOptions
  ): Promise<{ success: boolean; error?: string }> {
    try {
      // Step 1: Get authorization URL
      const { authorization_url } = await this.initiateOAuth(provider, service)

      // Decide open mode
      const isLocalhost = () =>
        typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
      const useRedirect = options?.mode === 'redirect' || (import.meta.env.DEV && isLocalhost())

      if (useRedirect) {
        // Open in the same window (dev-friendly). The callback pages will route back to /integrations.
        window.location.href = authorization_url
        return { success: true }
      }

      // Step 2: Open OAuth window and also start backend status polling as a robust fallback
      let popupRef: Window | null = null
      const messagePromise = this.openOAuthWindow(authorization_url, {
        onPopup: (w) => (popupRef = w)
      })

      const pollPromise = (async (): Promise<{ success: boolean; provider: string; error?: string }> => {
        const deadline = Date.now() + 120000 // 2 minutes
        // Poll every 1s until connected or timeout
        while (Date.now() < deadline) {
          try {
            const connections = await this.getOAuthConnections()
            const matched = connections.some((c) => c.provider === provider && c.service === service && c.connected)
            if (matched) {
              try {
                const pr = popupRef as Window | null
                if (pr && !(pr as any).closed) (pr as any).close()
              } catch {}
              return { success: true, provider }
            }
          } catch {
            // Ignore transient errors while polling
          }
          await new Promise((r) => setTimeout(r, 1000))
        }
        return { success: false, provider, error: 'OAuth timed out' }
      })()

      // Prefer any success. If the first result is a failure, wait for the other to complete before returning
      const tagged = (p: Promise<{ success: boolean; provider: string; error?: string }>, source: 'msg' | 'poll') =>
        p.then((r) => ({ r, source }))

      const first = await Promise.race([tagged(messagePromise, 'msg'), tagged(pollPromise, 'poll')])

      if (first.r.success) {
        return { success: true }
      }

      const other = await (first.source === 'msg' ? pollPromise : messagePromise)
      if (other.success) {
        return { success: true }
      }

      return { success: false, error: first.r.error || other.error || 'OAuth failed' }
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