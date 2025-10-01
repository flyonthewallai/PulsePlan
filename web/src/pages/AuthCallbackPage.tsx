import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'

export function AuthCallbackPage() {
  const navigate = useNavigate()

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        console.log('Handling auth callback...')
        console.log('Current URL:', window.location.href)
        console.log('Hash:', window.location.hash)
        console.log('Search:', window.location.search)

        // Get the URL hash and search params
        const hashParams = new URLSearchParams(window.location.hash.substring(1))
        const searchParams = new URLSearchParams(window.location.search)
        
        // Check for error in URL
        const error = hashParams.get('error') || searchParams.get('error')
        if (error) {
          console.error('OAuth error:', error)
          navigate('/auth?error=' + encodeURIComponent(error))
          return
        }

        // Wait a moment for Supabase to automatically process the callback
        // since we have detectSessionInUrl: true
        await new Promise(resolve => setTimeout(resolve, 1000))

        // Check if we have a session now
        const { data, error: authError } = await supabase.auth.getSession()
        
        if (authError) {
          console.error('Auth callback error:', authError)
          navigate('/auth?error=callback_failed')
          return
        }

        if (data.session) {
          console.log('Found session, redirecting to home')
          navigate('/')
        } else {
          console.log('No session found, redirecting to auth')
          navigate('/auth')
        }
      } catch (error) {
        console.error('Auth callback error:', error)
        navigate('/auth?error=callback_failed')
      }
    }

    handleAuthCallback()
  }, [navigate])

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-gray-600 border-t-blue-500 rounded-full animate-spin"></div>
    </div>
  )
}
