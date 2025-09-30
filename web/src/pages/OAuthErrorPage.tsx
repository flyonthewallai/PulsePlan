import React, { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { XCircle } from 'lucide-react'

export function OAuthErrorPage() {
  const [searchParams] = useSearchParams()
  const provider = searchParams.get('provider')
  const error = searchParams.get('error')

  useEffect(() => {
    // Send error message to parent window
    if (window.opener) {
      window.opener.postMessage({
        type: 'oauth-error',
        provider,
        error
      }, window.location.origin)
      window.close()
    }
  }, [provider, error])

  return (
    <div className="min-h-screen bg-neutral-900 flex items-center justify-center p-6">
      <div className="bg-neutral-800 border border-gray-700 rounded-xl p-8 max-w-md w-full text-center">
        <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-white mb-2">Connection Failed</h1>
        <p className="text-gray-400 mb-4">
          We couldn't connect your {provider} account.
        </p>
        {error && (
          <p className="text-sm text-red-400 mb-4">
            Error: {error}
          </p>
        )}
        <p className="text-xs text-gray-600">
          You can close this window and try again.
        </p>
      </div>
    </div>
  )
}