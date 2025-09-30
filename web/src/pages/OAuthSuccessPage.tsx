import React, { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CheckCircle } from 'lucide-react'

export function OAuthSuccessPage() {
  const [searchParams] = useSearchParams()
  const provider = searchParams.get('provider')
  const email = searchParams.get('email')

  useEffect(() => {
    // Send success message to parent window
    if (window.opener) {
      window.opener.postMessage({
        type: 'oauth-success',
        provider,
        email
      }, window.location.origin)
      window.close()
    }
  }, [provider, email])

  return (
    <div className="min-h-screen bg-neutral-900 flex items-center justify-center p-6">
      <div className="bg-neutral-800 border border-gray-700 rounded-xl p-8 max-w-md w-full text-center">
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-white mb-2">Success!</h1>
        <p className="text-gray-400 mb-4">
          Your {provider} account has been connected successfully.
        </p>
        {email && (
          <p className="text-sm text-gray-500">
            Connected account: {email}
          </p>
        )}
        <p className="text-xs text-gray-600 mt-4">
          You can close this window now.
        </p>
      </div>
    </div>
  )
}