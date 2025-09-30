import React, { useEffect, useState } from 'react'
import { supabase, getSession } from '../../lib/supabase'
import type { Session } from '@supabase/supabase-js'

interface AuthGateProps {
  children: React.ReactNode
  fallback: React.ReactNode
}

export function AuthGate({ children, fallback }: AuthGateProps) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    getSession().then(({ session }) => {
      setSession(session)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!session) {
    return <>{fallback}</>
  }

  return <>{children}</>
}