import React, { useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'

export function OAuthErrorPage() {
  const [searchParams] = useSearchParams()
  const provider = searchParams.get('provider')
  const error = searchParams.get('error')
  const hasExecuted = useRef(false)

  useEffect(() => {
    // Prevent double execution in React strict mode
    if (hasExecuted.current) return
    hasExecuted.current = true

    const timestamp = Date.now()
    
    // Use sessionStorage for temporary cross-window communication (better than localStorage)
    const result = {
      type: 'oauth-error',
      provider,
      error,
      timestamp
    }

    sessionStorage.setItem('oauth_result', JSON.stringify(result))

    // If opened as a popup, just close this window and let opener update UI
    if (window.opener && !window.opener.closed) {
      try {
        window.close()
      } catch (e) {
        // Silently fail if popup can't be closed
      }
      return
    }

    // Fallback for redirect-mode (no opener): navigate back to integrations immediately
    window.location.replace('/integrations')
  }, [provider, error])

  // Render nothing; this page is a pure handoff/redirect.
  return null
}