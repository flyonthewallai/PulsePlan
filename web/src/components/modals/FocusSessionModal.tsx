import React, { useState, useCallback, useEffect } from 'react'
import { X, Loader2, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import { components, typography, spacing, colors, cn as cnTokens } from '@/lib/design-tokens'
import { CommandInput } from '../commands'
import { useTasks } from '@/hooks/tasks'
import type { Task } from '@/lib/utils/types'
import { matchEntity } from '@/services/focus'

interface FocusSessionModalProps {
  isOpen: boolean
  onClose: () => void
  onStart: (config: FocusSessionConfig) => void
}

export interface FocusSessionConfig {
  task: Task | null
  taskName: string
  duration: number
  breakDuration: number
  cycles: number
}

const PRESET_DURATIONS = [25, 45, 60]
const PRESET_BREAKS = [5, 10, 15]

export function FocusSessionModal({ isOpen, onClose, onStart }: FocusSessionModalProps) {
  const [prompt, setPrompt] = useState('')
  const [isParsing, setIsParsing] = useState(false)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [taskSearchQuery, setTaskSearchQuery] = useState('')
  const [showTaskDropdown, setShowTaskDropdown] = useState(false)
  const [duration, setDuration] = useState(25)
  const [breakDuration, setBreakDuration] = useState(5)
  const [cycles, setCycles] = useState(1)
  
  const [useDefaultLengths, setUseDefaultLengths] = useState(true)

  const { data: tasks = [] } = useTasks()

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setPrompt('')
      setIsParsing(false)
      setSelectedTask(null)
      setTaskSearchQuery('')
      setShowTaskDropdown(false)
      setDuration(25)
      setBreakDuration(5)
      setCycles(1)
      
      setUseDefaultLengths(true)
    }
  }, [isOpen])

  const parsePrompt = useCallback(async (text: string) => {
    setIsParsing(true)
    
    try {
      // Extract duration first for backend hint
      const durationMatch = text.match(/(\d+)\s*(min|minute|minutes|hour|hours|hr|hrs)/i)
      let extractedDuration: number | undefined
      if (durationMatch) {
        let mins = parseInt(durationMatch[1])
        if (durationMatch[2].startsWith('h')) {
          mins *= 60
        }
        extractedDuration = Math.min(mins, 120)
        setDuration(extractedDuration)
      }

      // Call backend entity matching
      const matchedEntity = await matchEntity(text, extractedDuration)
      
      if (matchedEntity) {
        // Use the matched/created entity
        const taskName = matchedEntity.entity?.title || matchedEntity.entity?.name || text
        setTaskSearchQuery(taskName)
        
        let taskForSession = null
        
        // If it's a task, try to find it in the local tasks list
        if (matchedEntity.id && matchedEntity.type === 'task') {
          const localTask = tasks.find(t => t.id === matchedEntity.id)
          if (localTask) {
            taskForSession = localTask
          } else {
            // Create a minimal task object with the matched entity's ID
            taskForSession = {
              id: matchedEntity.id,
              title: taskName,
            } as Task
          }
        }
        
        // If duration was extracted from the prompt, use it
        if (extractedDuration) {
          setDuration(extractedDuration)
        }
        
        // Auto-start the session with the matched entity
        const config: FocusSessionConfig = {
          task: taskForSession,  // Use the task we just resolved
          taskName,
          duration: extractedDuration || duration,
          breakDuration,
          cycles,
        }
        
        onStart(config)
        onClose()
      } else {
        // Fallback to manual entry if no match
        
        const taskWords = text.replace(/\d+\s*(min|minute|hour|cycle|break|session)/gi, '').trim()
        setTaskSearchQuery(taskWords || text)
      }
    } catch (error) {
      console.error('Failed to match entity:', error)
      // Fallback to manual entry on error
      
      const taskWords = text.replace(/\d+\s*(min|minute|hour|cycle|break|session)/gi, '').trim()
      setTaskSearchQuery(taskWords || text)
    } finally {
      setIsParsing(false)
    }
  }, [tasks, duration, breakDuration, cycles, selectedTask, onStart, onClose])

  const handlePromptSubmit = useCallback(() => {
    if (!prompt.trim()) return
    parsePrompt(prompt.trim())
  }, [prompt, parsePrompt])

  const handleStart = useCallback(() => {
    const taskName = selectedTask?.title || taskSearchQuery || 'Focus Session'
    
    onStart({
      task: selectedTask,
      taskName,
      duration,
      breakDuration,
      cycles,
    })
    onClose()
  }, [selectedTask, taskSearchQuery, duration, breakDuration, cycles, onStart, onClose])

  const handleTaskSelect = (task: Task) => {
    setSelectedTask(task)
    setTaskSearchQuery(task.title)
    setShowTaskDropdown(false)
  }

  const handleTaskInputChange = (value: string) => {
    setTaskSearchQuery(value)
    setSelectedTask(null)
    setShowTaskDropdown(true)
  }

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }, [onClose])

  if (!isOpen) return null

  const pendingTasks = tasks.filter(t => t.status === 'pending')
  
  // Filter tasks based on search query
  const filteredTasks = taskSearchQuery.trim()
    ? pendingTasks.filter(t => 
        t.title.toLowerCase().includes(taskSearchQuery.toLowerCase())
      )
    : pendingTasks

  return (
    <>
      {/* Backdrop */}
      <div
        className={components.modal.overlay}
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[580px] max-w-[calc(100vw-32px)] max-h-[calc(100vh-64px)] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={cnTokens(components.modal.container, "w-full !mx-0 !max-w-none flex flex-col")}>
          {/* Header */}
          <div className={cnTokens(components.modal.header, "flex items-center justify-between")}>
            <div>
              <h2 className={components.modal.title}>Focus Session</h2>
              <p className={cnTokens(typography.body.small, colors.text.secondary, "mt-1")}>
                Tell me what you're working on and I'll match it to your tasks.
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className={components.modal.closeButton}
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className={cnTokens(components.modal.content, "flex-1 overflow-y-auto")}>
            {/* AI Input */}
          <div className={cnTokens(spacing.section.marginBottom)} onKeyDown={handleKeyDown}>
            <div className="relative">
              <CommandInput
                value={prompt}
                onChange={setPrompt}
                onSubmit={handlePromptSubmit}
                placeholder="Study for my biology exam for 45 minutes..."
                disabled={isParsing}
                showCommands={false}
              />
              {isParsing && (
                <div className={cnTokens("mt-2 flex items-center gap-2", typography.body.small, colors.text.secondary)}>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Matching to your tasks…</span>
                </div>
              )}
            </div>
            
            {/* Hint */}
            <p className={cnTokens("mt-2 text-center", typography.body.small, colors.text.tertiary)}>
              Press Enter to start • Esc to cancel
            </p>
          </div>

          {/* Divider - always visible */}
          <div className={cnTokens("relative", spacing.section.marginBottom)}>
            <div className="absolute inset-0 flex items-center">
              <div className={cnTokens("w-full", components.divider.horizontal)} />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className={cnTokens("bg-[#121212] px-2", colors.text.tertiary)}>or configure manually</span>
            </div>
          </div>

          {/* Manual Inputs */}
          <div className={spacing.stack.md}>
            {/* Task Selection - Searchable */}
            <div className="relative">
              <label className={components.input.label}>
                Task
              </label>
              <input
                type="text"
                value={taskSearchQuery}
                onChange={(e) => handleTaskInputChange(e.target.value)}
                onFocus={() => setShowTaskDropdown(true)}
                onBlur={() => {
                  // Delay to allow clicking on dropdown items
                  setTimeout(() => setShowTaskDropdown(false), 200)
                }}
                placeholder="Search or create a task..."
                className={cnTokens(components.input.base, "w-full")}
              />
              
              {/* Dropdown for task selection */}
              {showTaskDropdown && filteredTasks.length > 0 && (
                <div className={cnTokens("absolute z-10 w-full mt-1", "bg-neutral-800 border border-gray-700/50 rounded-lg", "max-h-48 overflow-y-auto shadow-lg")}>
                  {filteredTasks.map(task => (
                    <button
                      key={task.id}
                      type="button"
                      onClick={() => handleTaskSelect(task)}
                      className={cnTokens("w-full text-left px-3 py-2.5", typography.body.default, colors.text.primary, "hover:bg-neutral-700 transition-colors")}
                    >
                      {task.title}
                      {task.due_date && (
                        <span className={cnTokens(typography.body.small, colors.text.secondary, "ml-2")}>
                          • Due {new Date(task.due_date).toLocaleDateString()}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}
              
              {selectedTask && (
                <p className={components.input.helper}>
                  Selected task from your list
                </p>
              )}
            </div>

            {/* Use Default Lengths Toggle - custom checkbox, hover only on box */}
            <label className={cnTokens("flex items-center gap-3 cursor-default")}>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={useDefaultLengths}
                  onChange={(e) => setUseDefaultLengths(e.target.checked)}
                  className="peer sr-only"
                />
                <div className="w-5 h-5 border-2 border-gray-600 rounded bg-neutral-800/40 hover:border-gray-500 transition-colors peer-checked:bg-blue-600 peer-checked:border-blue-600">
                  {useDefaultLengths && (
                    <svg className="w-full h-full text-white" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </div>
              <span className={cnTokens(typography.body.default, colors.text.secondary)}>
                Use default lengths
              </span>
            </label>

            {/* Duration, Break, Cycles - Conditionally shown */}
            {!useDefaultLengths && (
              <>
                {/* Duration */}
                <div>
                  <label className={components.input.label}>
                    Duration (minutes)
                  </label>
                  <div className={cnTokens("flex gap-2", spacing.gap.sm)}>
                    {PRESET_DURATIONS.map(mins => (
                      <button
                        key={mins}
                        type="button"
                        onClick={() => setDuration(mins)}
                        className={cn(
                          cnTokens(components.button.base, "flex-1 py-2 px-3"),
                          duration === mins
                            ? 'bg-blue-600 text-white'
                            : cnTokens(components.button.secondary, "text-gray-300")
                        )}
                      >
                        {mins}
                      </button>
                    ))}
                    <input
                      type="number"
                      value={duration}
                      onChange={(e) => setDuration(Math.max(1, Math.min(120, parseInt(e.target.value) || 25)))}
                      className={cnTokens(components.input.base, "w-20 text-center")}
                      min="1"
                      max="120"
                    />
                  </div>
                </div>

                {/* Break Duration */}
                <div>
                  <label className={components.input.label}>
                    Break (minutes)
                  </label>
                  <div className={cnTokens("flex gap-2", spacing.gap.sm)}>
                    {PRESET_BREAKS.map(mins => (
                      <button
                        key={mins}
                        type="button"
                        onClick={() => setBreakDuration(mins)}
                        className={cn(
                          cnTokens(components.button.base, "flex-1 py-2 px-3"),
                          breakDuration === mins
                            ? 'bg-blue-600 text-white'
                            : cnTokens(components.button.secondary, "text-gray-300")
                        )}
                      >
                        {mins}
                      </button>
                    ))}
                    <input
                      type="number"
                      value={breakDuration}
                      onChange={(e) => setBreakDuration(Math.max(1, Math.min(30, parseInt(e.target.value) || 5)))}
                      className={cnTokens(components.input.base, "w-20 text-center")}
                      min="1"
                      max="30"
                    />
                  </div>
                </div>

                {/* Cycles */}
                <div>
                  <label className={components.input.label}>
                    Cycles
                  </label>
                  <select
                    value={cycles}
                    onChange={(e) => setCycles(parseInt(e.target.value))}
                    className={components.select.base}
                  >
                    {[1, 2, 3, 4, 5, 6].map(num => (
                      <option key={num} value={num}>
                        {num} {num === 1 ? 'cycle' : 'cycles'}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}
          </div>

          </div>

          {/* Footer */}
          <div className={components.modal.footer}>
            <button
              type="button"
              onClick={handleStart}
              disabled={!taskSearchQuery.trim()}
              className={cnTokens(
                components.button.base,
                components.button.primary,
                "w-full disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              Create Session
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

