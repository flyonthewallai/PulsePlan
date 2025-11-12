import { useState, useEffect, useCallback } from 'react'
import { Clock, Loader2, ArrowLeft, X } from 'lucide-react'
import { cn } from '../../lib/utils'
import { components, colors, spacing } from '../../lib/design-tokens'
import { durationPreferencesApi, type CourseDurationPreference, type DurationPreference } from '../../services/user/durationPreferencesService'
import { formatCourseCode } from '../../lib/utils/formatters'
import type { Course } from '../../services/user'

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

interface CourseDurationPreferencesSectionProps {
  course: Course
  onBack: () => void
}

export function CourseDurationPreferencesSection({ course, onBack }: CourseDurationPreferencesSectionProps) {
  const [coursePreferences, setCoursePreferences] = useState<Map<string, CourseDurationPreference>>(new Map())
  const [globalPreferences, setGlobalPreferences] = useState<Map<string, DurationPreference>>(new Map())
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  // Load both course and global preferences
  const loadPreferences = useCallback(async () => {
    try {
      setIsLoading(true)
      setSaveError(null)

      // Load course-specific preferences
      const coursePrefs = await durationPreferencesApi.getCoursePreferences(course.id)
      const coursePrefsMap = new Map<string, CourseDurationPreference>()
      coursePrefs.forEach((pref) => {
        coursePrefsMap.set(pref.category, pref)
      })
      setCoursePreferences(coursePrefsMap)

      // Load global preferences for fallback display
      const globalPrefs = await durationPreferencesApi.getGlobal()
      const globalPrefsMap = new Map<string, DurationPreference>()
      globalPrefs.forEach((pref) => {
        globalPrefsMap.set(pref.category, pref)
      })
      setGlobalPreferences(globalPrefsMap)
    } catch (error) {
      console.error('Failed to load course duration preferences:', error)
      setSaveError('Failed to load preferences')
    } finally {
      setIsLoading(false)
    }
  }, [course.id])

  useEffect(() => {
    loadPreferences()
  }, [loadPreferences])

  // Get effective value (course override, global, or default)
  const getEffectiveValue = useCallback((category: string): number => {
    // Check course-specific first
    const coursePref = coursePreferences.get(category)
    if (coursePref) {
      return coursePref.estimated_minutes
    }

    // Check global preference
    const globalPref = globalPreferences.get(category)
    if (globalPref) {
      return globalPref.estimated_minutes
    }

    // Return default
    const categoryDef = TASK_CATEGORIES.find((c) => c.value === category)
    return categoryDef?.defaultMinutes || 90
  }, [coursePreferences, globalPreferences])

  // Check if category has course override
  const hasCourseOverride = useCallback((category: string): boolean => {
    return coursePreferences.has(category)
  }, [coursePreferences])

  // Handle duration change
  const handleDurationChange = useCallback(async (category: string, minutes: number) => {
    try {
      setIsSaving(true)
      setSaveError(null)

      // Create or update course preference
      const updated = await durationPreferencesApi.createCoursePreference({
        course_id: course.id,
        category,
        estimated_minutes: minutes,
      })

      // Update local state
      setCoursePreferences((prev) => {
        const next = new Map(prev)
        next.set(category, updated)
        return next
      })
    } catch (error) {
      console.error('Failed to update course duration preference:', error)
      setSaveError('Failed to save preference')
    } finally {
      setIsSaving(false)
    }
  }, [course.id])

  // Handle "Use global" (delete override)
  const handleUseGlobal = useCallback(async (category: string) => {
    try {
      setIsSaving(true)
      setSaveError(null)

      // Delete course preference
      await durationPreferencesApi.deleteCoursePreference(course.id, category)

      // Update local state
      setCoursePreferences((prev) => {
        const next = new Map(prev)
        next.delete(category)
        return next
      })
    } catch (error) {
      console.error('Failed to delete course duration preference:', error)
      setSaveError('Failed to remove override')
    } finally {
      setIsSaving(false)
    }
  }, [course.id])

  const courseDisplayName = course.canvas_course_code 
    ? formatCourseCode(course.canvas_course_code) 
    : course.name

  if (isLoading) {
    return (
      <div className={cn(spacing.modal.content, 'flex items-center justify-center py-12')}>
        <div className="flex items-center gap-2 text-gray-400">
          <Loader2 size={16} className="animate-spin" />
          <span className="text-sm">Loading preferences...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={onBack}
          className={cn(components.iconButton.small, 'text-gray-400 hover:text-white')}
          aria-label="Back to courses"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div
            className="w-4 h-4 rounded-full shrink-0"
            style={{ backgroundColor: course.color }}
          />
          <h3 className={cn(typography.subsectionTitle, colors.text.primary, 'truncate')}>
            {courseDisplayName} Duration Preferences
          </h3>
        </div>
      </div>

      <p className={colors.text.secondary + ' text-sm'}>
        Set duration overrides for this course. These will override your global defaults for tasks in this course.
      </p>

      {saveError && (
        <div className={cn(components.badge.base, components.badge.danger, 'mb-4')}>
          {saveError}
        </div>
      )}

      <div className="space-y-3">
        {TASK_CATEGORIES.map((category) => {
          const effectiveValue = getEffectiveValue(category.value)
          const hasOverride = hasCourseOverride(category.value)
          const globalValue = globalPreferences.get(category.value)?.estimated_minutes || 
                            TASK_CATEGORIES.find((c) => c.value === category.value)?.defaultMinutes || 90

          return (
            <div
              key={category.value}
              className={cn(
                components.settingItem.base,
                hasOverride && 'border-blue-500/30',
                'flex items-center justify-between'
              )}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <Clock size={16} className={colors.text.tertiary + ' shrink-0'} />
                <div className="flex-1 min-w-0">
                  <p className={colors.text.primary + ' text-sm font-medium'}>
                    {category.label}
                    {hasOverride && (
                      <span className={colors.text.success + ' text-xs ml-2'}>
                        (Override)
                      </span>
                    )}
                  </p>
                  <p className={colors.text.secondary + ' text-xs mt-0.5'}>
                    Global: {globalValue} min
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 ml-4">
                <select
                  value={effectiveValue}
                  onChange={(e) => {
                    const minutes = parseInt(e.target.value, 10)
                    handleDurationChange(category.value, minutes)
                  }}
                  disabled={isSaving}
                  className={cn(
                    components.select.base,
                    'min-w-[120px]',
                    isSaving && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  {DURATION_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>

                {hasOverride && (
                  <button
                    onClick={() => handleUseGlobal(category.value)}
                    disabled={isSaving}
                    className={cn(
                      components.button.base,
                      components.button.ghost,
                      'px-2 py-1 text-xs',
                      isSaving && 'opacity-50 cursor-not-allowed'
                    )}
                    title="Use global default"
                  >
                    Use global
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className={cn(components.divider.horizontal, 'pt-4 mt-4')}>
        <p className={colors.text.tertiary + ' text-xs'}>
          Course overrides take precedence over global defaults. Use "Use global" to remove an override.
        </p>
      </div>
    </div>
  )
}

