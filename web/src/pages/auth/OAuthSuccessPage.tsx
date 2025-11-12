import React, { useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'

export function OAuthSuccessPage() {
  const [searchParams] = useSearchParams()
  const provider = searchParams.get('provider')
  const email = searchParams.get('email')
  const hasExecuted = useRef(false)

  useEffect(() => {
    // Prevent double execution in React strict mode
    if (hasExecuted.current) return
    hasExecuted.current = true

    const timestamp = Date.now()
    
    // Use sessionStorage for temporary cross-window communication (better than localStorage)
    const result = {
      type: 'oauth-success',
      provider,
      email,
      timestamp
    }

    sessionStorage.setItem('oauth_result', JSON.stringify(result))

    // If opened as a popup, send postMessage to opener AND close
    if (window.opener && !window.opener.closed) {
      try {
        window.opener.postMessage(result, window.location.origin)
        window.close()
      } catch (e) {
        // Silently fail if popup can't be closed
      }
      return
    }

    // Fallback for redirect-mode (no opener): navigate back to integrations immediately
    window.location.replace('/integrations')
  }, [provider, email])

  // Render nothing; this page is a pure handoff/redirect.
  return null
}