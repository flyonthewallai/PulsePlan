import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { signIn, signUp, signInWithGoogle, signInWithApple, signInWithMagicLink, resetPassword } from '../../lib/supabase'
import { cn } from '../../lib/utils'
import { config } from '../../lib/config'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

const signupSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  fullName: z.string().min(2, 'Full name must be at least 2 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

type LoginFormData = z.infer<typeof loginSchema>
type SignupFormData = z.infer<typeof signupSchema>

export function LoginPage() {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [showEmailForm, setShowEmailForm] = useState(false)

  // Debug configuration on mount
  useEffect(() => {
    console.log('LoginPage mounted')
    console.log('Supabase URL:', config.supabase.url)
    console.log('Supabase Anon Key:', config.supabase.anonKey ? 'Present' : 'Missing')
    console.log('API Base URL:', config.api.baseUrl)
    
    if (!config.supabase.url || !config.supabase.anonKey) {
      setError('Supabase configuration is missing. Please check your environment variables.')
    }
  }, [])

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  const signupForm = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      email: '',
      password: '',
      fullName: '',
      confirmPassword: '',
    },
  })

  const handleLogin = async (data: LoginFormData) => {
    console.log('Login attempt started:', data.email)
    setLoading(true)
    setError(null)
    
    try {
      console.log('Calling signIn function...')
      const { error } = await signIn(data.email, data.password)
      console.log('SignIn result:', { error })
      if (error) throw error
      console.log('Login successful!')
    } catch (err) {
      console.error('Login error:', err)
      setError(err instanceof Error ? err.message : 'Failed to sign in')
    } finally {
      setLoading(false)
    }
  }

  const handleSignup = async (data: SignupFormData) => {
    console.log('Signup attempt started:', data.email)
    setLoading(true)
    setError(null)
    
    try {
      console.log('Calling signUp function...')
      const { data: signupData, error } = await signUp(data.email, data.password, data.fullName)
      console.log('SignUp result:', { data: signupData, error })
      
      if (error) throw error
      
      // Check if user was created successfully
      if (signupData?.user) {
        console.log('User created successfully, signing in...')
        
        // Check if user needs email confirmation
        if (signupData.user.email_confirmed_at) {
          // User is already confirmed, sign them in immediately
          const { error: signInError } = await signIn(data.email, data.password)
          if (signInError) {
            console.error('Auto sign-in failed:', signInError)
            setError('Account created but failed to sign in automatically. Please try signing in manually.')
          } else {
            console.log('Auto sign-in successful!')
            setSuccess('Account created successfully! You are now signed in.')
          }
        } else {
          // User needs email confirmation, but we'll still try to sign them in
          // (this works if email confirmation is disabled in Supabase settings)
          const { error: signInError } = await signIn(data.email, data.password)
          if (signInError) {
            console.log('Email confirmation required, but trying anyway...')
            setSuccess('Account created! Please check your email to confirm your account, then sign in.')
          } else {
            console.log('Auto sign-in successful despite email confirmation!')
            setSuccess('Account created successfully! You are now signed in.')
          }
        }
      } else {
        setSuccess('Account created successfully! Please sign in.')
      }
    } catch (err) {
      console.error('Signup error:', err)
      setError(err instanceof Error ? err.message : 'Failed to sign up')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const { error } = await signInWithGoogle()
      if (error) throw error
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign in with Google')
    } finally {
      setLoading(false)
    }
  }

  const handleAppleSignIn = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const { error } = await signInWithApple()
      if (error) throw error
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign in with Apple')
    } finally {
      setLoading(false)
    }
  }

  const handleMagicLink = async (email: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const { error } = await signInWithMagicLink(email)
      if (error) throw error
      setSuccess('Check your email for a magic link!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send magic link')
    } finally {
      setLoading(false)
    }
  }

  const handleForgotPassword = async (email: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const { error } = await resetPassword(email)
      if (error) throw error
      setSuccess('Password reset instructions sent to your email!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reset email')
    } finally {
      setLoading(false)
    }
  }

  const currentForm = mode === 'login' ? loginForm : signupForm
  const onSubmit = mode === 'login' ? handleLogin : handleSignup

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-24 h-24 rounded-3xl mx-auto mb-3 overflow-hidden">
            <img 
              src="/icon.png" 
              alt="PulsePlan Logo"
              className="w-full h-full object-cover"
            />
          </div>
          <h1 className="text-3xl font-bold text-textPrimary mb-3 tracking-tight">PulsePlan</h1>
          <p className="text-textSecondary text-base font-medium">Your academic life, optimized.</p>
          <p className="text-xs text-textSecondary mt-1 font-normal">by Fly on the Wall LLC</p>
        </div>

        {error && (
          <div className="bg-error border border-error text-white px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-success/10 border border-success/20 text-success px-4 py-3 rounded-lg mb-4">
            {success}
          </div>
        )}

        {!showEmailForm ? (
          <div className="space-y-4 mb-6">
            {/* Social Auth Buttons */}
            <button
              onClick={handleGoogleSignIn}
              disabled={loading}
              className="w-full bg-[#2E2E2E] hover:bg-[#2E2E2E]/80 text-white font-semibold py-4 px-4 rounded-xl transition-colors flex items-center justify-center gap-3"
            >
              <svg className="w-6 h-6" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </button>

            <button
              onClick={handleAppleSignIn}
              disabled={loading}
              className="w-full bg-[#2E2E2E] hover:bg-[#2E2E2E]/80 text-white font-semibold py-4 px-4 rounded-xl transition-colors flex items-center justify-center gap-3"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/>
              </svg>
              Continue with Apple
            </button>

            <button
              onClick={() => setShowEmailForm(true)}
              disabled={loading}
              className="w-full bg-[#2E2E2E] hover:bg-[#2E2E2E]/80 text-white font-semibold py-4 px-4 rounded-xl transition-colors flex items-center justify-center gap-3"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Continue with Email
            </button>
          </div>
        ) : (
          <form onSubmit={currentForm.handleSubmit(onSubmit)} className="space-y-4">
            <div className="flex items-center gap-3 mb-4">
              <button
                type="button"
                onClick={() => setShowEmailForm(false)}
                className="p-2 text-primary hover:text-primary/80 -ml-2"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h2 className="text-xl font-bold text-textPrimary">
                {mode === 'login' ? 'Sign In' : 'Create Account'}
              </h2>
            </div>

            <div className="space-y-4 mb-4">
              {mode === 'signup' && (
                <div>
                  <input
                    {...signupForm.register('fullName')}
                    placeholder="Full Name"
                    disabled={loading}
                    className="w-full bg-surface text-textPrimary placeholder-textSecondary rounded-xl px-4 py-4 text-base focus:outline-none focus:ring-0 focus:border-none focus:shadow-none border-none outline-none"
                  />
                  {signupForm.formState.errors.fullName && (
                    <p className="bg-error text-white text-sm mt-2 px-2 py-1 rounded">{signupForm.formState.errors.fullName.message}</p>
                  )}
                </div>
              )}

              <div>
                <input
                  {...currentForm.register('email')}
                  type="email"
                  placeholder="Email"
                  disabled={loading}
                  autoCapitalize="none"
                  className="w-full bg-surface text-textPrimary placeholder-textSecondary rounded-xl px-4 py-4 text-base focus:outline-none focus:ring-2 focus:ring-primary border-none"
                />
                {currentForm.formState.errors.email && (
                  <p className="bg-error text-white text-sm mt-2 px-2 py-1 rounded">{currentForm.formState.errors.email.message}</p>
                )}
              </div>

              <div>
                <input
                  {...currentForm.register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  disabled={loading}
                  className="w-full bg-surface text-textPrimary placeholder-textSecondary rounded-xl px-4 py-4 text-base focus:outline-none focus:ring-2 focus:ring-primary border-none"
                />
                {currentForm.formState.errors.password && (
                  <p className="bg-error text-white text-sm mt-2 px-2 py-1 rounded">{currentForm.formState.errors.password.message}</p>
                )}
              </div>

              {mode === 'signup' && (
                <div>
                  <input
                    {...signupForm.register('confirmPassword')}
                    type="password"
                    placeholder="Confirm Password"
                    disabled={loading}
                    className="w-full bg-surface text-textPrimary placeholder-textSecondary rounded-xl px-4 py-4 text-base focus:outline-none focus:ring-0 focus:border-none focus:shadow-none border-none outline-none"
                  />
                  {signupForm.formState.errors.confirmPassword && (
                    <p className="bg-error text-white text-sm mt-2 px-2 py-1 rounded">{signupForm.formState.errors.confirmPassword.message}</p>
                  )}
                </div>
              )}
            </div>

            {mode === 'login' && (
              <div className="text-right mb-2">
                <button
                  type="button"
                  onClick={() => {
                    const email = loginForm.getValues('email')
                    if (email) handleForgotPassword(email)
                  }}
                  disabled={loading}
                  className="text-sm text-textSecondary hover:text-textPrimary font-medium"
                >
                  Forgot Password?
                </button>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !currentForm.formState.isValid}
              className={cn(
                "w-full bg-primary hover:bg-primary/90 text-white font-semibold py-4 px-4 rounded-2xl transition-colors min-h-[56px] flex items-center justify-center shadow-lg",
                (loading || !currentForm.formState.isValid) && "opacity-60 cursor-not-allowed"
              )}
              onClick={(e) => {
                console.log('Submit button clicked')
                console.log('Form valid:', currentForm.formState.isValid)
                console.log('Form errors:', currentForm.formState.errors)
                console.log('Form values:', currentForm.getValues())
              }}
            >
              {loading ? 'Loading...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>

            {mode === 'login' && (
              <button
                type="button"
                onClick={() => {
                  const email = loginForm.getValues('email')
                  if (email) handleMagicLink(email)
                }}
                disabled={loading}
                className="w-full text-center text-sm text-textSecondary hover:text-textPrimary py-2"
              >
                Sign in with Magic Link
              </button>
            )}

            <div className="text-center pt-4">
              <button
                type="button"
                onClick={() => {
                  setMode(mode === 'login' ? 'signup' : 'login')
                  setError(null)
                  setSuccess(null)
                }}
                disabled={loading}
                className="text-textSecondary hover:text-textPrimary"
              >
                {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
                <span className="text-primary font-medium">
                  {mode === 'login' ? 'Sign Up' : 'Sign In'}
                </span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}