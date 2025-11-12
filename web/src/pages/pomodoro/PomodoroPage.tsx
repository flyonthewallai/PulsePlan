import { useEffect, useState, useRef, useCallback } from 'react'
import { Play, Pause, RotateCcw, Settings, Target, CheckSquare, Calendar, X } from 'lucide-react'
import { FlipClock } from '@/components/ui/common'
import { FocusSessionModal, type FocusSessionConfig } from '@/components/modals'
import { PomodoroSettingsModal, type PomodoroSettings, DEFAULT_SETTINGS } from '@/components/modals'
import { 
  startFocusSession, 
  endFocusSession, 
  getActiveSession,
  startPhase,
  endPhase,
  getPomodoroSettings,
  putPomodoroSettings,
  type FocusSession,
  type MatchedEntity,
  type PhaseType,
  type PomodoroSettings as ServerPomodoroSettings,
} from '@/services/focus'
import { supabase } from '@/lib/supabase'

const SETTINGS_KEY = 'pulseplan_pomodoro_settings'

export function PomodoroPage() {
  const [settings, setSettings] = useState<PomodoroSettings>(() => {
    const saved = localStorage.getItem(SETTINGS_KEY)
    return saved ? JSON.parse(saved) : DEFAULT_SETTINGS
  })
  // Load server settings on mount; keep localStorage as fast fallback
  useEffect(() => {
    let mounted = true
    getPomodoroSettings().then((remote) => {
      if (!mounted) return
      const merged = {
        defaultDuration: remote.focus_minutes,
        defaultBreak: remote.break_minutes,
        cyclesPerSession: remote.cycles_per_session,
        autoStartNextSession: remote.auto_start_next_session,
        autoStartBreaks: remote.auto_start_breaks,
        playSoundOnComplete: remote.play_sound_on_complete,
        desktopNotifications: remote.desktop_notifications,
      }
      setSettings(merged)
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(merged))
    }).catch(() => void 0)
    return () => { mounted = false }
  }, [])

  const [secondsLeft, setSecondsLeft] = useState(settings.defaultDuration * 60)
  const [isRunning, setIsRunning] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [currentTask, setCurrentTask] = useState<{ name: string; id?: string } | null>(null)
  const [showFocusModal, setShowFocusModal] = useState(false)
  const [showSettingsModal, setShowSettingsModal] = useState(false)
  const [matchedEntity, setMatchedEntity] = useState<MatchedEntity | null>(null)
  // Phase tracking state (client-managed)
  const [phaseMode, setPhaseMode] = useState(false)
  const [phaseId, setPhaseId] = useState<string | null>(null)
  const [focusCount, setFocusCount] = useState(0)
  const [recentPhases, setRecentPhases] = useState<Array<{ type: PhaseType; status: 'completed' | 'current' | 'upcoming'; id?: string }>>([])
  
  const handlePlayPause = () => {
    if (!currentTask) {
      setShowFocusModal(true)
      return
    }
    setIsRunning(prev => !prev)
    if (isComplete) setIsComplete(false)
  }

  const handleSessionCancel = async () => {
    if (!activeSession) return
    
    try {
      await endFocusSession(activeSession.id, {
        was_completed: false,
        interruption_count: interruptions
      })
      console.log('Focus session cancelled:', activeSession.id)
    } catch (error) {
      console.error('Failed to end focus session:', error)
    }
    
    setActiveSession(null)
  }

  const handleReset = () => {
    // Reset timer to the session's max (expected_duration) but keep session
    const targetSeconds = activeSession
      ? (activeSession.expected_duration * 60)
      : (settings.defaultDuration * 60)
    setSecondsLeft(targetSeconds)
    setIsComplete(false)
    setIsRunning(false)
    setInterruptions(0)
  }

  const handleClear = async () => {
    // Clear everything and cancel session
    setIsRunning(false)
    setSecondsLeft(settings.defaultDuration * 60)
    setIsComplete(false)
    setCurrentTask(null)
    setMatchedEntity(null)
    setInterruptions(0)
    
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    
    // Cancel active session if exists
    if (activeSession) {
      await handleSessionCancel()
    }
  }
  const intervalRef = useRef<number | null>(null)
  const [activeSession, setActiveSession] = useState<FocusSession | null>(null)
  const [interruptions, setInterruptions] = useState(0)

  const getNextPhase = useCallback((current: PhaseType, focusDoneCount: number): PhaseType => {
    if (current === 'focus') {
      const nextIsLong = ((focusDoneCount + 1) % settings.cyclesPerSession) === 0
      return nextIsLong ? 'long_break' : 'break'
    }
    return 'focus'
  }, [settings.cyclesPerSession])

  const getPhaseSeconds = useCallback((type: PhaseType): number => {
    if (type === 'focus') return settings.defaultDuration * 60
    if (type === 'break') return settings.defaultBreak * 60
    const longBreakMin = Math.max(settings.defaultBreak * 2, 10)
    return longBreakMin * 60
  }, [settings.defaultDuration, settings.defaultBreak])

  const onPhaseComplete = useCallback(async () => {
    const currentType: PhaseType = recentPhases.length > 0 ? recentPhases[recentPhases.length - 1].type : 'focus'
    if (phaseId) {
      try { await endPhase({ phase_id: phaseId, interrupted: false }) } catch {}
    }
    setRecentPhases(prev => {
      const maxLen = settings.cyclesPerSession * 2 - 1
      const copy = prev.map((p, idx, arr) => idx === arr.length - 1 ? { ...p, status: 'completed' as const } : p)
      return copy.slice(-maxLen)
    })

    let newFocusCount = focusCount
    if (currentType === 'focus') newFocusCount = focusCount + 1
    setFocusCount(newFocusCount)

    const nextType = getNextPhase(currentType, focusCount)
    const nextSeconds = getPhaseSeconds(nextType)
    setSecondsLeft(nextSeconds)

    const shouldAutoStart = (nextType === 'focus') ? settings.autoStartNextSession : settings.autoStartBreaks
    if (activeSession) {
      try {
        const started = await startPhase({
          session_id: activeSession.id,
          phase_type: nextType,
          expected_duration_minutes: Math.round(nextSeconds / 60)
        })
        setPhaseId(started.phase.id)
        setRecentPhases(prev => {
          const maxLen = settings.cyclesPerSession * 2 - 1
          const updated = [...prev, { type: nextType, status: 'current' as const, id: started.phase.id }]
          return updated.slice(-maxLen)
        })
      } catch (e) {
        console.error('Failed to start next phase', e)
        setPhaseId(null)
      }
    }

    setIsComplete(false)
    setIsRunning(shouldAutoStart)
  }, [phaseId, focusCount, activeSession, settings, recentPhases])

  // Play completion sound using Web Audio API
  const playCompletionSound = useCallback(() => {
    if (!settings.playSoundOnComplete) return
    
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      oscillator.frequency.value = 800
      oscillator.type = 'sine'
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)
      
      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.5)
    } catch (e) {
      console.log('Audio playback not available')
    }
  }, [settings.playSoundOnComplete])

  // Show desktop notification
  const showNotification = useCallback(() => {
    if (!settings.desktopNotifications) return

    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Focus Session Complete! 🎉', {
        body: currentTask ? `Great work on "${currentTask.name}"!` : 'Time for a break!',
        icon: '/favicon.ico',
      })
    }
  }, [settings.desktopNotifications, currentTask])

  // Request notification permission and check for active session on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }

    // Check if there's an active session from backend
    const checkActiveSession = async () => {
      try {
        const session = await getActiveSession()
        if (session) {
          console.log('Found active session, resuming:', session)
          setActiveSession(session)
          setCurrentTask({ 
            name: session.context || 'Focus session', 
            id: session.task_id 
          })
          
          // Calculate remaining time
          const startTime = new Date(session.actual_start_time || session.start_time)
          const elapsed = Math.floor((Date.now() - startTime.getTime()) / 1000)
          const remaining = Math.max(0, (session.expected_duration * 60) - elapsed)
          
          setSecondsLeft(remaining)
          
          // Don't auto-resume, just show it's resumable
          console.log('Session resumable with', remaining, 'seconds remaining')
        }
      } catch (error) {
        console.error('Error checking active session:', error)
      }
    }

    checkActiveSession()
  }, [])

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current)
    }
  }, [])

  // Timer logic with proper 1-second intervals
  useEffect(() => {
    if (!isRunning) {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    // Update timer every second
    intervalRef.current = window.setInterval(() => {
      setSecondsLeft(prev => {
        if (prev <= 1) {
          if (phaseMode && activeSession) {
            playCompletionSound()
            showNotification()
            void onPhaseComplete()
            return 0
          } else {
            setIsRunning(false)
            setIsComplete(true)
            playCompletionSound()
            showNotification()
            // End session in backend
            handleSessionComplete()
            return 0
          }
        }
        return prev - 1
      })
    }, 1000)
    
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [isRunning, playCompletionSound, showNotification, phaseMode, activeSession, onPhaseComplete])

  

  const handleFocusStart = async (config: FocusSessionConfig) => {
    setCurrentTask({ 
      name: config.taskName, 
      id: config.task?.id 
    })
    setSecondsLeft(config.duration * 60)
    setInterruptions(0)
    setIsComplete(false)
    
    // Start session in backend
    try {
      const result = await startFocusSession({
        expected_duration: config.duration,
        task_id: config.task?.id,
        context: config.taskName,
        session_type: 'pomodoro',
        auto_match_entity: true // Enable entity matching
      })
      setActiveSession(result.session)
      console.log('Focus session started:', result.session.id)
      
      // Store matched entity if available
      if (result.matched_entity) {
        setMatchedEntity(result.matched_entity)
        console.log(
          'Matched to:', result.matched_entity.type,
          result.matched_entity.entity?.title || result.matched_entity.entity?.name,
          `(confidence: ${(result.matched_entity.confidence * 100).toFixed(0)}%)`
        )
      }

      // Start first phase (focus)
      try {
        const started = await startPhase({
          session_id: result.session.id,
          phase_type: 'focus',
          expected_duration_minutes: config.duration
        })
        setPhaseId(started.phase.id)
        setPhaseMode(true)
        setFocusCount(0)
        setRecentPhases([{ type: 'focus', status: 'current', id: started.phase.id }])
      } catch (e) {
        console.error('Failed to start phase', e)
      }
    } catch (error) {
      console.error('Failed to start focus session:', error)
      // Continue with local timer even if backend fails
    }
    
    setIsRunning(true)
  }

  const handleSessionComplete = async () => {
    if (!activeSession) return
    
    try {
      await endFocusSession(activeSession.id, {
        was_completed: true,
        interruption_count: interruptions,
        focus_score: undefined // Can prompt user later
      })
      console.log('Focus session completed:', activeSession.id)
    } catch (error) {
      console.error('Failed to end focus session:', error)
    }
    
    setActiveSession(null)
  }

  

  

  const handleSaveSettings = (newSettings: PomodoroSettings) => {
    setSettings(newSettings)
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(newSettings))
    // Fire-and-forget persist to server
    const payload: ServerPomodoroSettings = {
      focus_minutes: newSettings.defaultDuration,
      break_minutes: newSettings.defaultBreak,
      long_break_minutes: Math.max(newSettings.defaultBreak * 2, 10),
      cycles_per_session: newSettings.cyclesPerSession,
      auto_start_breaks: newSettings.autoStartBreaks,
      auto_start_next_session: newSettings.autoStartNextSession,
      play_sound_on_complete: newSettings.playSoundOnComplete,
      desktop_notifications: newSettings.desktopNotifications,
    }
    void putPomodoroSettings(payload)
  }

  const minutes = Math.floor(secondsLeft / 60)
  const seconds = secondsLeft % 60
  const totalSeconds = settings.defaultDuration * 60
  const progress = ((totalSeconds - secondsLeft) / totalSeconds) * 100

  // Phase tracking (selector UI only): do not modify existing progress bar or timer
  const activeIndex: number = (activeSession?.session_type === 'break') ? 1 : 0 // 0: Focus, 1: Break, 2: Long Break
  const phaseLabels = ['Focus', 'Break', 'Long Break']
  const currentPhaseLabel = phaseLabels[activeIndex]

  // Current cycle number display (#n)
  const cycleNumber = (() => {
    const focusPhases = recentPhases.filter(p => p.type === 'focus').length
    if (focusPhases === 0 && phaseMode) return 1
    return Math.max(1, focusPhases)
  })()
  const displayPhaseLabel = (() => {
    const last = recentPhases[recentPhases.length - 1]
    if (!last) return 'Focus'
    if (last.type === 'long_break') return 'Long Break'
    return last.type.charAt(0).toUpperCase() + last.type.slice(1)
  })()

  // Update document title with timer status (Pomodoro app style)
  useEffect(() => {
    if (currentTask && isRunning) {
      const formattedMinutes = String(minutes).padStart(2, '0')
      const formattedSeconds = String(seconds).padStart(2, '0')
      document.title = `${formattedMinutes}:${formattedSeconds} - ${currentPhaseLabel} | PulsePlan`
    } else if (currentTask && !isRunning && !isComplete) {
      const formattedMinutes = String(minutes).padStart(2, '0')
      const formattedSeconds = String(seconds).padStart(2, '0')
      document.title = `${formattedMinutes}:${formattedSeconds} - ${currentPhaseLabel} (Paused) | PulsePlan`
    } else if (currentTask && isComplete) {
      document.title = `Complete - ${currentPhaseLabel} | PulsePlan`
    } else {
      document.title = 'PulsePlan - Pomodoro Timer'
    }

    // Cleanup: reset title on unmount
    return () => {
      document.title = 'PulsePlan'
    }
  }, [minutes, seconds, currentTask, isRunning, isComplete, currentPhaseLabel])

  // Realtime: subscribe to focus_session_phases for this session
  useEffect(() => {
    if (!activeSession) return
    const channel = supabase.channel(`phases-${activeSession.id}`)
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'focus_session_phases',
        filter: `session_id=eq.${activeSession.id}`
      }, (payload: any) => {
        const row = payload.new || payload.old
        if (!row) return
        // If a phase got its ended_at, mark current as completed and prep next placeholder
        if (row.ended_at) {
          setRecentPhases(prev => prev.map((p, idx, arr) => idx === arr.length - 1 ? { ...p, status: 'completed' as const } : p))
        } else if (payload.eventType === 'INSERT') {
          // New phase started
          setRecentPhases(prev => [...prev, { type: row.phase_type, status: 'current' as const, id: row.id }])
        }
      })
      .subscribe()
    return () => { void supabase.removeChannel(channel) }
  }, [activeSession])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 relative" style={{ backgroundColor: '#0f0f0f' }}>
      

      {/* Main Content */}
      <div className="flex flex-col items-center">
        {/* Timer Display - FlipClock as the main design */}
        <div className="mb-8 flex flex-col items-center">
          <FlipClock minutes={minutes} seconds={seconds} />
        </div>

        {/* Inline cycle/phase label centered under timer */}
        {currentTask && (
          <div className="w-[600px] max-w-[calc(100vw-48px)] -mt-2 mb-4">
            <div className="text-center text-sm text-gray-300">
              {`Cycle #${cycleNumber}`} <span className="mx-2">•</span> {displayPhaseLabel}
            </div>
          </div>
        )}

        {/* Progress Bar */}
        {currentTask && (
          <div className="w-[600px] max-w-[calc(100vw-48px)] mb-8">
            <div className="h-1.5 bg-neutral-800/60 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        

        {/* Phase selector (moved below progress bar) */}
        <div className="w-[600px] max-w-[calc(100vw-48px)] mb-6">
          <div className="relative w-full rounded-lg border border-white/10 bg-white/5 h-8 overflow-hidden">
            {/* Slider */}
            <div
              className="absolute top-0 bottom-0 left-0 rounded-md bg-white/90 shadow transition-transform duration-300 ease-out"
              style={{
                width: '33.3333%',
                transform: `translateX(${activeIndex * 100}%)`
              }}
            />
            {/* Options */}
            <div className="relative z-[1] grid grid-cols-3 h-full">
              <div className={`flex items-center justify-center text-xs font-medium uppercase tracking-wide ${activeIndex === 0 ? 'text-neutral-900' : 'text-gray-300'}`}>Focus</div>
              <div className={`flex items-center justify-center text-xs font-medium uppercase tracking-wide ${activeIndex === 1 ? 'text-neutral-900' : 'text-gray-300'}`}>Break</div>
              <div className={`flex items-center justify-center text-xs font-medium uppercase tracking-wide ${activeIndex === 2 ? 'text-neutral-900' : 'text-gray-300'}`}>Long Break</div>
            </div>
          </div>
        </div>

        {/* Current Task Display Card (moved below selector) */}
        {currentTask && (
          <div className="mb-8 w-[600px] max-w-[calc(100vw-48px)]">
            <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4">
              {/* Task Title with Bullet */}
              <div className="flex items-center gap-3 mb-3">
                <div className="w-2 h-2 bg-white rounded-full flex-shrink-0"></div>
                <h3 className="text-white font-medium text-base leading-tight flex-1">
                  {currentTask.name}
                </h3>
              </div>

              {/* Reserved for task body; tracker moved below card */}
              
              {/* Matched Entity Info */}
              {matchedEntity && (
                <div className="ml-5 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Target size={14} />
                    <span>
                      {matchedEntity.auto_created ? 'Created new' : 'Linked to'} {matchedEntity.type}
                      {matchedEntity.confidence && !matchedEntity.auto_created && (
                        <span className="ml-1 text-gray-500">
                          ({(matchedEntity.confidence * 100).toFixed(0)}% match)
                        </span>
                      )}
                    </span>
                  </div>
                  
                  {/* Entity Type Icon */}
                  <div className="w-5 h-5 bg-white rounded-full flex items-center justify-center flex-shrink-0">
                    {matchedEntity.type === 'task' || matchedEntity.type === 'exam' || matchedEntity.type === 'assignment' ? (
                      <CheckSquare size={12} className="text-neutral-800" />
                    ) : matchedEntity.type === 'timeblock' ? (
                      <Calendar size={12} className="text-neutral-800" />
                    ) : (
                      <Target size={12} className="text-neutral-800" />
                    )}
                  </div>
                </div>
              )}
              
              {/* Fallback if no matched entity */}
              {!matchedEntity && (
                <div className="ml-5 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Target size={14} />
                    <span>Focus Session</span>
                  </div>
                  
                  <div className="w-5 h-5 bg-white rounded-full flex items-center justify-center flex-shrink-0">
                    <Target size={12} className="text-neutral-800" />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Circle trail tracker below the task card */}

        {/* Divider between task card and actions */}
        {currentTask && (
          <div className="w-[600px] max-w-[calc(100vw-48px)] mb-3">
            <div className="h-px bg-white/10" />
          </div>
        )}

        {/* Primary Action Card (center) */}
        <div className="mt-4">
          <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl shadow-lg backdrop-blur-sm p-3 flex items-center gap-3">
            {/* Start/Pause */}
            <button
              onClick={handlePlayPause}
              className="p-2 rounded-lg flex items-center justify-center text-gray-300 hover:text-white transition-colors hover:bg-white/5 hover:opacity-80"
              aria-label={isRunning ? 'Pause session' : (currentTask ? (isComplete ? 'Start again' : 'Resume session') : 'Start focus session')}
            >
              {isRunning ? (
                <Pause size={18} className="text-current" />
              ) : (
                <Play size={18} className="text-current" />
              )}
            </button>

            {/* Reset to session max time (keeps session) */}
            {currentTask && (
              <button
                onClick={handleReset}
                className="p-2 rounded-lg flex items-center justify-center text-gray-300 hover:text-white transition-colors hover:bg-white/5 hover:opacity-80"
                aria-label="Reset timer to full session time"
                title="Reset timer to full session time"
              >
                <RotateCcw size={18} className="text-current" />
              </button>
            )}

            {/* Clear everything and cancel session */}
            {currentTask && (
              <button
                onClick={handleClear}
                className="p-2 rounded-lg flex items-center justify-center text-gray-300 hover:text-white transition-colors hover:bg-white/5 hover:opacity-80"
                aria-label="Clear session and cancel"
                title="Clear session and cancel"
              >
                <X size={18} className="text-current" />
              </button>
            )}

            {/* Settings */}
            <button
              onClick={() => setShowSettingsModal(true)}
              className="p-2 rounded-lg flex items-center justify-center text-gray-300 hover:text-white transition-colors hover:bg-white/5 hover:opacity-80"
              aria-label="Settings"
            >
              <Settings size={18} className="text-current" />
            </button>
          </div>
        </div>

        
      </div>

      

      {/* Modals */}
      <FocusSessionModal
        isOpen={showFocusModal}
        onClose={() => setShowFocusModal(false)}
        onStart={handleFocusStart}
      />

      <PomodoroSettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        settings={settings}
        onSave={handleSaveSettings}
      />
    </div>
  )
}

export default PomodoroPage


