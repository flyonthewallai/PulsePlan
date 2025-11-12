import { useState, useEffect, useCallback } from 'react'
import { Clock, Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'
import { components, colors, spacing } from '../../lib/design-tokens'
import { durationPreferencesApi, type DurationPreference } from '../../services/user/durationPreferencesService'

// Task categories with default durations (from backend)
const TASK_CATEGORIES = [
  { value: 'assignment', label: 'Assignments', defaultMinutes: 120 },
  { value: 'reading', label: 'Readings', defaultMinutes: 60 },
  { value: 'study', label: 'Study Sessions', defaultMinutes: 90 },
  { value: 'exam_prep', label: 'Exam Prep', defaultMinutes: 150 },
  { value: 'project', label: 'Projects', defaultMinutes: 180 },
  { value: 'quiz', label: 'Quizzes', defaultMinutes: 30 },
  { value: 'lab', label: 'Labs', defaultMinutes: 120 },
] as const

// Duration options in minutes
const DURATION_OPTIONS = [
  { value: 15, label: '15 min' },
  { value: 30, label: '30 min' },
  { value: 45, label: '45 min' },
  { value: 60, label: '1 hour' },
  { value: 90, label: '1.5 hours' },
  { value: 120, label: '2 hours' },
  { value: 150, label: '2.5 hours' },
  { value: 180, label: '3 hours' },
  { value: 240, label: '4 hours' },
] as const

interface DurationPreferencesSectionProps {
  // No props needed - component manages its own state
}

export function DurationPreferencesSection({}: DurationPreferencesSectionProps) {
  const [preferences, setPreferences] = useState<Map<string, DurationPreference>>(new Map())
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  // Load preferences
  const loadPreferences = useCallback(async () => {
    try {
      setIsLoading(true)
      setSaveError(null)
      const prefs = await durationPreferencesApi.getGlobal()
      
      // Convert to Map for easy lookup
      const prefsMap = new Map<string, DurationPreference>()
      prefs.forEach((pref) => {
        prefsMap.set(pref.category, pref)
      })
      
      setPreferences(prefsMap)
    } catch (error) {
      console.error('Failed to load duration preferences:', error)
      setSaveError('Failed to load preferences')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPreferences()
  }, [loadPreferences])

  // Get current value for a category (preference or default)
  const getCurrentValue = useCallback((category: string): number => {
    const pref = preferences.get(category)
    if (pref) {
      return pref.estimated_minutes
    }
    // Return default from TASK_CATEGORIES
    const categoryDef = TASK_CATEGORIES.find((c) => c.value === category)
    return categoryDef?.defaultMinutes || 90
  }, [preferences])

  // Handle duration change
  const handleDurationChange = useCallback(async (category: string, minutes: number) => {
    try {
      setIsSaving(true)
      setSaveError(null)

      // Update preference via API
      const updated = await durationPreferencesApi.updateGlobal(category, minutes)

      // Update local state
      setPreferences((prev) => {
        const next = new Map(prev)
        next.set(category, updated)
        return next
      })
    } catch (error) {
      console.error('Failed to update duration preference:', error)
      setSaveError('Failed to save preference')
    } finally {
      setIsSaving(false)
    }
  }, [])

  if (isLoading) {
    return (
      <div className={cn(spacing.modal.content, 'flex items-center justify-center py-12')}>
        <div className="flex items-center gap-2 text-gray-400">
          <Loader2 size={16} className="animate-spin" />
          <span className="text-sm">Loading duration preferences...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <p className={colors.text.secondary + ' text-sm'}>
        Set default estimated durations for different task types. These will be used when creating new tasks unless you override them per course.
      </p>

      {saveError && (
        <div className={cn(components.badge.base, components.badge.danger, 'mb-4')}>
          {saveError}
        </div>
      )}

      <div className="space-y-3">
        {TASK_CATEGORIES.map((category) => {
          const currentValue = getCurrentValue(category.value)
          const hasCustomValue = preferences.has(category.value)

          return (
            <div
              key={category.value}
              className={cn(components.settingItem.base, 'flex items-center justify-between')}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <Clock size={16} className={colors.text.tertiary + ' shrink-0'} />
                <div className="flex-1 min-w-0">
                  <p className={colors.text.primary + ' text-sm font-medium'}>
                    {category.label}
                  </p>
                  {hasCustomValue && (
                    <p className={colors.text.secondary + ' text-xs mt-0.5'}>
                      Custom (default: {category.defaultMinutes} min)
                    </p>
                  )}
                </div>
              </div>

              <select
                value={currentValue}
                onChange={(e) => {
                  const minutes = parseInt(e.target.value, 10)
                  handleDurationChange(category.value, minutes)
                }}
                disabled={isSaving}
                className={cn(
                  components.select.base,
                  'ml-4 min-w-[120px]',
                  isSaving && 'opacity-50 cursor-not-allowed'
                )}
              >
                {DURATION_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          )
        })}
      </div>

      <div className={cn(components.divider.horizontal, 'pt-4 mt-4')}>
        <p className={colors.text.tertiary + ' text-xs'}>
          These defaults apply to all courses unless you set course-specific overrides.
        </p>
      </div>
    </div>
  )
}

