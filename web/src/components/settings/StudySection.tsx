import { Sun, Moon } from 'lucide-react'
import { cn } from '../../lib/utils'

interface StudySectionProps {
  studyStartHour: number
  setStudyStartHour: (value: number) => void
  studyEndHour: number
  setStudyEndHour: (value: number) => void
}

export function StudySection({
  studyStartHour,
  setStudyStartHour,
  studyEndHour,
  setStudyEndHour,
}: StudySectionProps) {
  const formatTime = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM'
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
    return `${displayHour}:00 ${period}`
  }

  return (
    <div className="space-y-4">
      <p className="text-gray-400 text-sm">
        Set your preferred study hours. PulsePlan will schedule tasks and send reminders during these times.
      </p>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-3">
            <Sun size={24} className="text-blue-500" />
            <div className="flex-1">
              <p className="text-xs text-gray-400 mb-1">Start Time</p>
              <p className="text-lg font-semibold text-white">{formatTime(studyStartHour)}</p>
            </div>
          </div>
          <input
            type="range"
            min="0"
            max="23"
            value={studyStartHour}
            onChange={(e) => setStudyStartHour(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            style={{
              accentColor: '#3b82f6'
            }}
          />
        </div>

        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-3">
            <Moon size={24} className="text-blue-500" />
            <div className="flex-1">
              <p className="text-xs text-gray-400 mb-1">End Time</p>
              <p className="text-lg font-semibold text-white">{formatTime(studyEndHour)}</p>
            </div>
          </div>
          <input
            type="range"
            min="0"
            max="23"
            value={studyEndHour}
            onChange={(e) => setStudyEndHour(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            style={{
              accentColor: '#3b82f6'
            }}
          />
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Daily Schedule</h3>
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4">
          <div className="flex justify-between text-xs text-gray-400 mb-2">
            <span>12 AM</span>
            <span>12 PM</span>
            <span>11 PM</span>
          </div>
          <div className="flex h-6 bg-neutral-900 rounded-lg overflow-hidden">
            {Array.from({ length: 24 }).map((_, hour) => {
              const isInRange =
                studyStartHour <= studyEndHour
                  ? hour >= studyStartHour && hour <= studyEndHour
                  : hour >= studyStartHour || hour <= studyEndHour
              return (
                <div
                  key={hour}
                  className={cn(
                    'flex-1 border-r border-gray-800/50',
                    isInRange ? 'bg-blue-500' : 'bg-transparent'
                  )}
                />
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

