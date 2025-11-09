import { X, Clock, Calendar, Zap, Edit, Check, Music, Camera, Book, Gamepad2, Palette, Target, MountainSnow, Heart, Bike, Dumbbell, Mountain } from 'lucide-react'
import { cn } from '../lib/utils'
import { typography, components, spacing } from '../lib/design-tokens'

interface ParsedHobby {
  name: string
  preferred_time: 'morning' | 'afternoon' | 'evening' | 'night' | 'any'
  specific_time: { start: string; end: string } | null
  days: string[]
  duration: { min: number; max: number }
  flexibility: 'low' | 'medium' | 'high'
  notes: string
  icon: 'Music' | 'Camera' | 'Book' | 'Gamepad2' | 'Palette' | 'Target' | 'MountainSnow' | 'Heart' | 'Bike' | 'Dumbbell' | 'Mountain'
}

interface HobbySummaryProps {
  isOpen: boolean
  hobby: ParsedHobby | null
  confidence: number
  onClose: () => void
  onConfirm: () => void
  onEdit: () => void
  isLoading?: boolean
}

const getHobbyIcon = (icon: ParsedHobby['icon'], className?: string) => {
  const props = { size: 20, className: cn('text-white', className) }
  switch (icon) {
    case 'Music': return <Music {...props} />
    case 'Camera': return <Camera {...props} />
    case 'Book': return <Book {...props} />
    case 'Gamepad2': return <Gamepad2 {...props} />
    case 'Palette': return <Palette {...props} />
    case 'MountainSnow': return <MountainSnow {...props} />
    case 'Heart': return <Heart {...props} />
    case 'Bike': return <Bike {...props} />
    case 'Dumbbell': return <Dumbbell {...props} />
    case 'Mountain': return <Mountain {...props} />
    default: return <Target {...props} />
  }
}

const formatTime24to12 = (time24: string): string => {
  const [hours, minutes] = time24.split(':').map(Number)
  const period = hours >= 12 ? 'PM' : 'AM'
  const hours12 = hours % 12 || 12
  return `${hours12}:${minutes.toString().padStart(2, '0')} ${period}`
}

const formatTimeOfDay = (time: ParsedHobby['preferred_time'], specificTime: ParsedHobby['specific_time']): string => {
  if (specificTime) {
    return `${formatTime24to12(specificTime.start)} - ${formatTime24to12(specificTime.end)}`
  }

  const map = {
    morning: 'Morning (5am-11am)',
    afternoon: 'Afternoon (12pm-4pm)',
    evening: 'Evening (5pm-8pm)',
    night: 'Night (9pm-12am)',
    any: 'Anytime'
  }
  return map[time]
}

const formatDays = (days: string[]): string => {
  if (days.length === 7) return 'Every day'
  if (days.length === 5 && !days.includes('Sat') && !days.includes('Sun')) {
    return 'Weekdays (Mon-Fri)'
  }
  if (days.length === 2 && days.includes('Sat') && days.includes('Sun')) {
    return 'Weekends'
  }
  return days.join(', ')
}

const formatDuration = (duration: { min: number; max: number }): string => {
  if (duration.min === duration.max) {
    return `${duration.min} min`
  }
  return `${duration.min}–${duration.max} min`
}

const formatFlexibility = (flexibility: ParsedHobby['flexibility']): string => {
  const map = {
    low: 'Low (strict timing)',
    medium: 'Medium (somewhat flexible)',
    high: 'High (very flexible)'
  }
  return map[flexibility]
}

export function HobbySummary({
  isOpen,
  hobby,
  confidence,
  onClose,
  onConfirm,
  onEdit,
  isLoading
}: HobbySummaryProps) {
  if (!isOpen || !hobby) return null

  const isLowConfidence = confidence < 0.7

  return (
    <div className={components.modal.overlay}>
      <div className={cn(components.modal.container, "max-w-md")}>
        {/* Header */}
        <div className={components.modal.header}>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                {getHobbyIcon(hobby.icon)}
              </div>
              <div>
                <h3 className={components.modal.title}>{hobby.name}</h3>
                {isLowConfidence && (
                  <p className="text-xs text-yellow-400">Please review the details below</p>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className={components.modal.closeButton}
              disabled={isLoading}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Summary Content */}
        <div className={cn(components.modal.content, spacing.stack.md)}>
          <p className="text-gray-400 text-sm">
            Here's what I understood from your description:
          </p>

          {/* Details Grid */}
          <div className="space-y-2">
            {/* Preferred Time */}
            <div className="flex items-start gap-3 p-3 bg-neutral-800/40 border border-gray-700/40 rounded-lg">
              <Clock size={16} className="text-blue-400 mt-0.5" />
              <div className="flex-1">
                <div className="text-xs text-gray-400 mb-1">
                  {hobby.specific_time ? 'Specific Time' : 'Preferred Time'}
                </div>
                <div className="text-sm text-white font-medium">
                  {formatTimeOfDay(hobby.preferred_time, hobby.specific_time)}
                </div>
              </div>
            </div>

            {/* Days */}
            <div className="flex items-start gap-3 p-3 bg-neutral-800/40 border border-gray-700/40 rounded-lg">
              <Calendar size={16} className="text-green-400 mt-0.5" />
              <div className="flex-1">
                <div className="text-xs text-gray-400 mb-1">Days</div>
                <div className="text-sm text-white font-medium">
                  {formatDays(hobby.days)}
                </div>
              </div>
            </div>

            {/* Duration */}
            <div className="flex items-start gap-3 p-3 bg-neutral-800/40 border border-gray-700/40 rounded-lg">
              <Clock size={16} className="text-purple-400 mt-0.5" />
              <div className="flex-1">
                <div className="text-xs text-gray-400 mb-1">Duration</div>
                <div className="text-sm text-white font-medium">
                  {formatDuration(hobby.duration)}
                </div>
              </div>
            </div>

            {/* Flexibility */}
            <div className="flex items-start gap-3 p-3 bg-neutral-800/40 border border-gray-700/40 rounded-lg">
              <Zap size={16} className="text-yellow-400 mt-0.5" />
              <div className="flex-1">
                <div className="text-xs text-gray-400 mb-1">Flexibility</div>
                <div className="text-sm text-white font-medium">
                  {formatFlexibility(hobby.flexibility)}
                </div>
              </div>
            </div>

            {/* Notes (if present) */}
            {hobby.notes && (
              <div className="flex items-start gap-3 p-3 bg-neutral-800/40 border border-gray-700/40 rounded-lg">
                <div className="text-xs text-gray-400 mb-1">Notes</div>
                <div className="text-sm text-gray-300 italic">
                  "{hobby.notes}"
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className={components.modal.footer}>
          <button
            onClick={onEdit}
            disabled={isLoading}
            className={cn(
              components.button.base,
              components.button.secondary,
              "flex items-center gap-2",
              isLoading && "opacity-50 cursor-not-allowed"
            )}
          >
            <Edit size={14} />
            Edit details
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={cn(
              components.button.base,
              components.button.primary,
              "flex items-center gap-2",
              isLoading && "opacity-50 cursor-not-allowed"
            )}
          >
            <Check size={14} />
            Looks good
          </button>
        </div>
      </div>
    </div>
  )
}
