import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { X, Loader2 } from 'lucide-react'
import { cn } from '../../../lib/utils'
import { format } from 'date-fns'
import { CommandInput } from '../../../components/commands'

interface AIEventPromptProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (prompt: string) => Promise<void>
  timeSlot: {
    start: string
    end: string
  } | null
  position?: {
    x: number
    y: number
  }
  className?: string
}

/**
 * AI-driven event creation prompt
 * Displays a compact input box when user drags on calendar
 * Replaces the traditional form modal with natural language input
 *
 * Performance optimizations:
 * - Memoized to prevent unnecessary re-renders
 * - Callbacks are memoized with useCallback
 * - Expensive computations use useMemo
 * - Command parsing disabled when not needed
 */
export const AIEventPrompt = React.memo(function AIEventPrompt({
  isOpen,
  onClose,
  onSubmit,
  timeSlot,
  position,
  className,
}: AIEventPromptProps) {
  const [prompt, setPrompt] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLDivElement>(null)

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      // Prefill with /schedule when opening for helpful affordance
      setPrompt('')
    }
  }, [isOpen])

  // Reset state when closed
  useEffect(() => {
    if (!isOpen) {
      setPrompt('')
      setError(null)
      setIsSubmitting(false)
    }
  }, [isOpen])

  // Memoize submit handler to prevent re-creating on every render
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault()
    }

    if (!prompt.trim() || !timeSlot) {
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      await onSubmit(prompt.trim())
      onClose()
    } catch (err) {
      console.error('Error creating event:', err)
      setError('Failed to create event. Please try again.')
      setIsSubmitting(false)
    }
  }, [prompt, timeSlot, onSubmit, onClose])

  // Memoize keydown handler
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }, [onClose])

  // Memoize formatted time to avoid re-computing on every render
  const formattedTime = useMemo(() => {
    if (!timeSlot) return null
    return `${format(new Date(timeSlot.start), 'h:mm a')} - ${format(new Date(timeSlot.end), 'h:mm a')}`
  }, [timeSlot])

  if (!isOpen || !timeSlot) return null

  // Calculate position (default to center if no position provided)
  const style: React.CSSProperties = position
    ? {
        position: 'fixed',
        left: `${Math.min(position.x, window.innerWidth - 400)}px`,
        top: `${Math.min(position.y, window.innerHeight - 200)}px`,
        zIndex: 9999,
      }
    : {
        position: 'fixed',
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 9999,
      }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-[2px] z-[9998]"
        onClick={onClose}
      />

      {/* Prompt Box */}
      <div
        style={style}
        className={cn(
          'bg-[#121212] text-[#E5E5E5] rounded-2xl shadow-2xl border border-white/10',
          'w-[560px] max-w-[calc(100vw-32px)]',
          'animate-in fade-in slide-in-from-bottom-2 duration-150',
          className
        )}
      >
        <form onSubmit={(e) => handleSubmit(e)} className="p-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs text-gray-400">
              {formattedTime}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded-md hover:bg-white/5 transition-colors"
              disabled={isSubmitting}
              aria-label="Close"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>

          {/* Chatbox input */}
          <div ref={inputRef} onKeyDown={handleKeyDown}>
            <CommandInput
              value={prompt}
              onChange={setPrompt}
              onSubmit={() => handleSubmit()}
              placeholder="What would you like me to schedule?"
              disabled={isSubmitting}
              showCommands={false}
            />
            {isSubmitting && (
              <div className="mt-2 flex items-center gap-2 text-xs text-gray-400">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Creating…
              </div>
            )}
          </div>

          {/* Error message */}
          {error && (
            <div className="mt-2 text-xs text-red-400">
              {error}
            </div>
          )}
          {/* Hint */}
          <p className="mt-2 text-[10px] text-center text-gray-500">
            Press Enter to create • Esc to cancel
          </p>
        </form>
      </div>
    </>
  )
})

