import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { signIn, signUp, signInWithGoogle, signInWithApple, signInWithMagicLink, resetPassword } from '@/lib/supabase'
import { cn } from '@/lib/utils'
import { config } from '@/lib/config'
import { Mail, Lock, User, Eye, EyeOff, ArrowLeft, Calendar, CheckCircle, Clock, Bell, Check, BookOpen, List } from 'lucide-react'

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

// Sample data for the stacked cards graphic
const sampleCards = [
  {
    id: 1,
    type: 'email',
    title: 'New Email',
    content: {
      to: 'prof.smith@university.edu',
      subject: 'Question about Final Project',
      body: 'Hi Professor Smith, I hope you\'re doing well. I have a question about the final project requirements. Could we schedule a quick meeting this week to discuss the scope? Thank you for your time.'
    },
    zIndex: 1,
    transform: 'translate(-120px, -120px)'
  },
  {
    id: 2,
    type: 'assignments',
    title: 'Assignments',
    content: {
      items: [
        {
          id: '1',
          title: 'Research Paper - Machine Learning',
          completed: false,
          due_date: '2024-01-20T23:59:00Z',
          course_code: 'CS 401'
        },
        {
          id: '2',
          title: 'Database Design Project',
          completed: false,
          due_date: '2024-01-18T17:00:00Z',
          course_code: 'CS 350'
        },
        {
          id: '3',
          title: 'Linear Algebra Problem Set 5',
          completed: true,
          due_date: '2024-01-15T11:59:00Z',
          course_code: 'MATH 301'
        }
      ]
    },
    zIndex: 4,
    transform: 'translate(120px, -120px)'
  },
  {
    id: 3,
    type: 'events',
    title: 'Events',
    content: {
      today: [
        { time: '9:00 am', text: 'Calculus Final Exam' },
        { time: '2:00 pm', text: 'Job Interview - Tech Corp' },
        { time: '4:30 pm', text: 'Study Group Meeting' }
      ],
      tomorrow: [
        { time: '10:00 am', text: 'Research Presentation' }
      ]
    },
    zIndex: 2,
    transform: 'translate(-120px, 120px)'
  },
  {
    id: 4,
    type: 'todos',
    title: 'To-dos',
    content: {
      items: [
        { 
          id: '1',
          title: 'Gym workout - Upper body', 
          completed: false, 
          due_date: '2024-01-15T16:00:00Z',
          displayTime: '4:00 PM'
        },
        { 
          id: '2',
          title: 'Prepare internship application', 
          completed: false, 
          due_date: '2024-01-20T12:00:00Z',
          displayTime: '12:00 PM'
        },
        { 
          id: '3',
          title: 'Grocery shopping', 
          completed: false, 
          due_date: '2024-01-18T19:00:00Z',
          displayTime: '7:00 PM'
        },
        { 
          id: '4',
          title: 'Call mom', 
          completed: true, 
          due_date: '2024-01-12T10:00:00Z',
          displayTime: '10:00 AM'
        }
      ]
    },
    zIndex: 3,
    transform: 'translate(120px, 120px)'
  }
]

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [showEmailForm, setShowEmailForm] = useState(false)

  // Validate configuration on mount
  useEffect(() => {
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
    setLoading(true)
    setError(null)
    
    try {
      const { error } = await signIn(data.email, data.password)
      if (error) throw error
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign in')
    } finally {
      setLoading(false)
    }
  }

  const handleSignup = async (data: SignupFormData) => {
    setLoading(true)
    setError(null)
    
    try {
      const { data: signupData, error } = await signUp(data.email, data.password, data.fullName)
      
      if (error) throw error
      
      // Check if user was created successfully
      if (signupData?.user) {
        // Check if user needs email confirmation
        if (signupData.user.email_confirmed_at) {
          // User is already confirmed, sign them in immediately
          const { error: signInError } = await signIn(data.email, data.password)
          if (signInError) {
            setError('Account created but failed to sign in automatically. Please try signing in manually.')
          } else {
            setSuccess('Account created successfully! You are now signed in.')
          }
        } else {
          // User needs email confirmation, but we'll still try to sign them in
          // (this works if email confirmation is disabled in Supabase settings)
          const { error: signInError } = await signIn(data.email, data.password)
          if (signInError) {
            setSuccess('Account created! Please check your email to confirm your account, then sign in.')
          } else {
            setSuccess('Account created successfully! You are now signed in.')
          }
        }
      } else {
        setSuccess('Account created successfully! Please sign in.')
      }
    } catch (err) {
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

  const renderCard = (card: typeof sampleCards[0]) => {
    switch (card.type) {
      case 'email':
        return (
          <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4 w-80">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">{card.title}</h3>
              <div className="flex gap-1">
                <div className="w-3 h-3 bg-gray-600 rounded-full"></div>
                <div className="w-3 h-3 bg-gray-600 rounded-full"></div>
                <div className="w-3 h-3 bg-gray-600 rounded-full"></div>
              </div>
            </div>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-400 mb-1">To:</div>
                <div className="text-sm text-white">{card.content.to}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Subject:</div>
                <div className="text-sm text-white">{card.content.subject}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Message:</div>
                <div className="text-sm text-blue-300 leading-relaxed">{card.content.body}</div>
              </div>
            </div>
          </div>
        )
      
      case 'assignments':
        return (
          <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4 w-80">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">{card.title}</h3>
              <div className="w-4 h-4 flex items-center justify-center">
                <BookOpen size={16} className="text-gray-400" />
              </div>
            </div>
            <div className="space-y-3">
              {card.content.items.map((assignment) => (
                <div key={assignment.id} className="flex items-start gap-3">
                  <button
                    className={`w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                      assignment.completed
                        ? 'bg-green-500 border-green-500' 
                        : 'border-gray-500'
                    }`}
                  >
                    {assignment.completed && (
                      <span className="text-white text-xs font-semibold">✓</span>
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium leading-tight ${
                      assignment.completed 
                        ? 'line-through text-gray-400' 
                        : 'text-white'
                    }`}>
                      {assignment.title}
                    </div>
                    <div className="flex items-center gap-3 mt-1 flex-wrap">
                      <div className="flex items-center gap-1">
                        <Calendar size={10} className="text-gray-400" />
                        <span className="text-xs text-gray-400">
                          {new Date(assignment.due_date).toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric' 
                          })}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock size={10} className="text-gray-400" />
                        <span className="text-xs text-gray-400">
                          {new Date(assignment.due_date).toLocaleTimeString('en-US', {
                            hour: 'numeric',
                            minute: '2-digit',
                            hour12: true
                          })}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <BookOpen size={10} className="text-gray-400" />
                        <span className="text-xs text-gray-400">
                          {assignment.course_code}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      
      case 'events':
        return (
          <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4 w-80">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">{card.title}</h3>
              <div className="w-4 h-4 flex items-center justify-center">
                <Calendar size={16} className="text-gray-400" />
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <div className="text-sm font-medium text-gray-400 mb-2">Today</div>
                <div className="space-y-2">
                  {card.content.today.map((event, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span className="text-xs text-gray-400">{event.time}</span>
                      <span className="text-sm text-white">{event.text}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-400 mb-2">Tomorrow</div>
                <div className="space-y-2">
                  {card.content.tomorrow.map((event, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span className="text-xs text-gray-400">{event.time}</span>
                      <span className="text-sm text-white">{event.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )
      
      case 'todos':
        return (
          <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4 w-80">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">{card.title}</h3>
              <div className="w-4 h-4 flex items-center justify-center">
                <List size={16} className="text-gray-400" />
              </div>
            </div>
            <div className="space-y-3">
              {card.content.items.map((todo) => (
                <div key={todo.id} className="flex items-start gap-3">
                  <button
                    className={`w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                      todo.completed
                        ? 'bg-green-500 border-green-500' 
                        : 'border-gray-500'
                    }`}
                  >
                    {todo.completed && (
                      <Check size={8} className="text-white" strokeWidth={3} />
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium leading-tight ${
                      todo.completed 
                        ? 'line-through text-gray-400' 
                        : 'text-white'
                    }`}>
                      {todo.title}
                    </div>
                    {todo.due_date && (
                      <div className="flex items-center gap-3 mt-1 flex-wrap">
                        <div className="flex items-center gap-1">
                          <Calendar size={10} className="text-gray-400" />
                          <span className="text-xs text-gray-400">
                            {new Date(todo.due_date).toLocaleDateString('en-US', { 
                              month: 'short', 
                              day: 'numeric' 
                            })}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock size={10} className="text-gray-400" />
                          <span className="text-xs text-gray-400">
                            {todo.displayTime || new Date(todo.due_date).toLocaleTimeString('en-US', {
                              hour: 'numeric',
                              minute: '2-digit',
                              hour12: true
                            })}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-black flex relative">
      {/* Background Split */}
      <div className="absolute inset-0 flex">
        <div className="flex-1 bg-black"></div>
        <div className="w-px bg-gray-800"></div>
        <div className="flex-1 bg-gray-900"></div>
      </div>
      
      {/* Left Side - Auth Form */}
      <div className="flex-1 flex items-center justify-center p-8 pl-48 relative z-10">
        <div className="w-full max-w-md">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl mx-auto mb-4 overflow-hidden">
              <img 
                src="/icon.png" 
                alt="PulsePlan Logo"
                className="w-full h-full object-cover"
              />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Try PulsePlan for free!</h1>
            <p className="text-gray-400 text-base">Log in with Google or Apple</p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl mb-4">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-500/10 border border-green-500/20 text-green-400 px-4 py-3 rounded-xl mb-4">
              {success}
            </div>
          )}

          {!showEmailForm ? (
            <div className="space-y-3 mb-6">
              {/* Social Auth Buttons */}
              <button
                onClick={handleGoogleSignIn}
                disabled={loading}
                className="w-full bg-neutral-800/80 hover:bg-neutral-800 border border-gray-700/50 text-white font-medium py-3 px-4 rounded-xl transition-colors flex items-center justify-center gap-3"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
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
                className="w-full bg-neutral-800/80 hover:bg-neutral-800 border border-gray-700/50 text-white font-medium py-3 px-4 rounded-xl transition-colors flex items-center justify-center gap-3"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/>
                </svg>
                Continue with Apple
              </button>

              <button
                onClick={() => setShowEmailForm(true)}
                disabled={loading}
                className="w-full bg-neutral-800/80 hover:bg-neutral-800 border border-gray-700/50 text-white font-medium py-3 px-4 rounded-xl transition-colors flex items-center justify-center gap-3"
              >
                <Mail size={20} />
                Continue with Email
              </button>

              {/* Privacy and Terms */}
              <div className="text-center mt-6">
                <p className="text-xs text-gray-500">
                  By continuing, you agree to our{' '}
                  <a href="#" className="text-blue-400 hover:text-blue-300 transition-colors">
                    Privacy Policy
                  </a>{' '}
                  and{' '}
                  <a href="#" className="text-blue-400 hover:text-blue-300 transition-colors">
                    Terms of Service
                  </a>
                </p>
              </div>
            </div>
          ) : (
            <form onSubmit={currentForm.handleSubmit(onSubmit)} className="space-y-4">
              <div className="flex items-center gap-3 mb-4">
                <button
                  type="button"
                  onClick={() => setShowEmailForm(false)}
                  className="p-2 text-gray-400 hover:text-white transition-colors"
                >
                  <ArrowLeft size={20} />
                </button>
                <h2 className="text-lg font-semibold text-white">
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
                      className="w-full bg-neutral-800/80 border border-gray-700/50 text-white placeholder-gray-400 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-gray-600"
                    />
                    {signupForm.formState.errors.fullName && (
                      <p className="text-red-400 text-xs mt-1">{signupForm.formState.errors.fullName.message}</p>
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
                    className="w-full bg-neutral-800/80 border border-gray-700/50 text-white placeholder-gray-400 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-gray-600"
                  />
                  {currentForm.formState.errors.email && (
                    <p className="text-red-400 text-xs mt-1">{currentForm.formState.errors.email.message}</p>
                  )}
                </div>

                <div className="relative">
                  <input
                    {...currentForm.register('password')}
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Password"
                    disabled={loading}
                    className="w-full bg-neutral-800/80 border border-gray-700/50 text-white placeholder-gray-400 rounded-xl px-4 py-3 pr-12 text-sm focus:outline-none focus:border-gray-600"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                  {currentForm.formState.errors.password && (
                    <p className="text-red-400 text-xs mt-1">{currentForm.formState.errors.password.message}</p>
                  )}
                </div>

                {mode === 'signup' && (
                  <div>
                    <input
                      {...signupForm.register('confirmPassword')}
                      type="password"
                      placeholder="Confirm Password"
                      disabled={loading}
                      className="w-full bg-neutral-800/80 border border-gray-700/50 text-white placeholder-gray-400 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-gray-600"
                    />
                    {signupForm.formState.errors.confirmPassword && (
                      <p className="text-red-400 text-xs mt-1">{signupForm.formState.errors.confirmPassword.message}</p>
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
                    className="text-xs text-gray-400 hover:text-white transition-colors"
                  >
                    Forgot Password?
                  </button>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !currentForm.formState.isValid}
                className={cn(
                  "w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-xl transition-colors min-h-[48px] flex items-center justify-center",
                  (loading || !currentForm.formState.isValid) && "opacity-60 cursor-not-allowed"
                )}
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
                  className="w-full text-center text-xs text-gray-400 hover:text-white py-2 transition-colors"
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
                  className="text-gray-400 hover:text-white transition-colors text-sm"
                >
                  {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
                  <span className="text-blue-400 font-medium">
                    {mode === 'login' ? 'Sign Up' : 'Sign In'}
                  </span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Right Side - Stacked Cards Graphic */}
      <div className="flex-1 flex flex-col items-center justify-center p-8 pr-48 relative overflow-hidden z-10">
        <div className="relative w-[500px] h-[500px] flex items-center justify-center mb-4">
          {sampleCards.map((card) => (
            <div
              key={card.id}
              className="absolute transition-all duration-300 hover:scale-105"
              style={{
                zIndex: card.zIndex,
                transform: card.transform,
              }}
            >
              {renderCard(card)}
            </div>
          ))}
        </div>
        
        {/* Calendar Card - Medium Width */}
        <div className="w-[600px]">
          <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">Calendar</h3>
              <div className="w-4 h-4 flex items-center justify-center">
                <Calendar size={16} className="text-gray-400" />
              </div>
            </div>
            
            <div className="space-y-3">
              {/* Today Section */}
              <div>
                <div className="text-sm font-medium text-white mb-2">Today</div>
                <div className="space-y-2">
                  <div className="relative">
                    <div className="flex items-center gap-3 py-2">
                      {/* Vertical blue line for timed events */}
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-full"></div>
                      
                      <div className="flex-1 ml-6">
                        <div className="text-sm text-white font-medium">CSCI 1300 - Lecture</div>
                        <div className="text-xs text-gray-400">8 - 9AM</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tomorrow Section */}
              <div>
                <div className="text-sm font-medium text-white mb-2">Tomorrow</div>
                <div className="space-y-2">
                  <div className="relative">
                    <div className="flex items-center gap-3 py-2">
                      {/* Blue dot for all-day events */}
                      <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 ml-1"></div>
                      
                      <div className="flex-1 ml-6">
                        <div className="text-sm text-white font-medium">Career Fair</div>
                        <div className="text-xs text-gray-400">All day</div>
                      </div>
                    </div>
                  </div>
                  <div className="relative">
                    <div className="flex items-center gap-3 py-2">
                      {/* Vertical blue line for timed events */}
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-full"></div>
                      
                      <div className="flex-1 ml-6">
                        <div className="text-sm text-white font-medium">Professor Office Hours</div>
                        <div className="text-xs text-gray-400">2:00 - 3:30PM</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* View all link */}
            <div className="mt-3 pt-2">
              <button className="text-xs text-gray-400 hover:text-white transition-colors">
                View all events →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
