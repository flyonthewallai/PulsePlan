import { useState } from 'react'
import { Mail, Calendar } from 'lucide-react'
import { cn } from '../../lib/utils'
import { typography, components } from '../../lib/design-tokens'
import { ToggleSwitch } from './ToggleSwitch'

interface WeeklyPulseSectionProps {
  isWeeklyPulseEnabled: boolean
  setIsWeeklyPulseEnabled: (value: boolean) => void
  weeklyPulseDay: 'sunday' | 'monday' | 'friday'
  setWeeklyPulseDay: (value: 'sunday' | 'monday' | 'friday') => void
  upcomingTasksContent: string
  setUpcomingTasksContent: (value: string) => void
  overdueItemsContent: string
  setOverdueItemsContent: (value: string) => void
  studyHabitsContent: string
  setStudyHabitsContent: (value: string) => void
  streaksContent: string
  setStreaksContent: (value: string) => void
  optionalPulseContent: string
  setOptionalPulseContent: (value: string) => void
}

export function WeeklyPulseSection({
  isWeeklyPulseEnabled,
  setIsWeeklyPulseEnabled,
  weeklyPulseDay,
  setWeeklyPulseDay,
  upcomingTasksContent,
  setUpcomingTasksContent,
  overdueItemsContent,
  setOverdueItemsContent,
  studyHabitsContent,
  setStudyHabitsContent,
  streaksContent,
  setStreaksContent,
  optionalPulseContent,
  setOptionalPulseContent,
}: WeeklyPulseSectionProps) {
  const [showDaySelection, setShowDaySelection] = useState(false)

  const getDayDisplayValue = () => {
    const time = '6:00 AM'
    switch (weeklyPulseDay) {
      case 'sunday': return `Sunday, ${time}`
      case 'monday': return `Monday, ${time}`
      case 'friday': return `Friday, ${time}`
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-gray-400 text-sm">
        Customize your weekly recap email by defining what you want to receive in each section
      </p>

      <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
        <ToggleSwitch
          enabled={isWeeklyPulseEnabled}
          onToggle={() => setIsWeeklyPulseEnabled(!isWeeklyPulseEnabled)}
          label="Weekly Pulse Enabled"
          icon={<Mail size={18} className="text-gray-400" />}
        />
        <div className="p-4 flex items-center justify-between border-t border-gray-700/30">
          <div className="flex items-center gap-3">
            <Calendar size={18} className="text-gray-400" />
            <div>
              <div className="text-white text-sm font-medium">Delivery Schedule</div>
            </div>
          </div>
          <button
            onClick={() => setShowDaySelection(!showDaySelection)}
            className="text-xs text-gray-400 hover:text-white transition-colors"
            disabled={!isWeeklyPulseEnabled}
          >
            {isWeeklyPulseEnabled ? getDayDisplayValue() : 'None'}
          </button>
        </div>
      </div>

      {showDaySelection && isWeeklyPulseEnabled && (
        <div className="space-y-2">
          <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Delivery Day</h3>
          <div className="flex gap-2">
            {(['sunday', 'monday', 'friday'] as const).map((day) => (
              <button
                key={day}
                onClick={() => setWeeklyPulseDay(day)}
                className={cn(
                  "flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors border",
                  weeklyPulseDay === day
                    ? "bg-blue-500 text-white border-blue-500"
                    : "bg-neutral-800/40 text-white border-gray-700/50 hover:bg-neutral-800/60"
                )}
              >
                {day.charAt(0).toUpperCase() + day.slice(1)}
              </button>
            ))}
          </div>
        </div>
      )}

      {isWeeklyPulseEnabled && (
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
          <div className="p-4 text-center border-b border-gray-700/50">
            <h3 className="text-sm font-semibold text-white mb-0.5">The Weekly Pulse</h3>
            <p className="text-xs text-gray-400 italic">Your Personalized Academic Digest</p>
          </div>

          <div className="p-4 space-y-3">
            <div>
              <h4 className={cn(typography.subsectionTitle, "mb-2")}>Upcoming Tasks</h4>
              <textarea
                value={upcomingTasksContent}
                onChange={(e) => setUpcomingTasksContent(e.target.value)}
                className={cn(components.textarea.base, "w-full min-h-[50px]")}
                placeholder="Describe what you want to see for upcoming tasks..."
              />
            </div>

            <div>
              <h4 className={cn(typography.subsectionTitle, "mb-2")}>Overdue Items</h4>
              <textarea
                value={overdueItemsContent}
                onChange={(e) => setOverdueItemsContent(e.target.value)}
                className={cn(components.textarea.base, "w-full min-h-[50px]")}
                placeholder="Describe what you want to see for overdue items..."
              />
            </div>

            <div>
              <h4 className={cn(typography.subsectionTitle, "mb-2")}>Study Habits Summary</h4>
              <textarea
                value={studyHabitsContent}
                onChange={(e) => setStudyHabitsContent(e.target.value)}
                className={cn(components.textarea.base, "w-full min-h-[50px]")}
                placeholder="Describe what insights you want about your study habits..."
              />
            </div>

            <div>
              <h4 className={cn(typography.subsectionTitle, "mb-2")}>Personal Streaks & Milestones</h4>
              <textarea
                value={streaksContent}
                onChange={(e) => setStreaksContent(e.target.value)}
                className={cn(components.textarea.base, "w-full min-h-[50px]")}
                placeholder="Describe what achievements and progress you want to see..."
              />
            </div>

            <div>
              <h4 className={cn(typography.subsectionTitle, "mb-2")}>Optional Content</h4>
              <textarea
                value={optionalPulseContent}
                onChange={(e) => setOptionalPulseContent(e.target.value)}
                className={cn(components.textarea.base, "w-full min-h-[50px]")}
                placeholder="Add any additional content you'd like to receive (leave blank if not needed)..."
              />
            </div>
          </div>
        </div>
      )}

      <div className="bg-neutral-800/40 border border-gray-700/50 rounded-lg p-4">
        <p className="text-xs text-gray-400 text-center leading-relaxed">
          {isWeeklyPulseEnabled
            ? `Your Weekly Pulse will be delivered every ${weeklyPulseDay.charAt(0).toUpperCase() + weeklyPulseDay.slice(1)} at 6:00 AM. Customize each section above to receive exactly the insights you need.`
            : 'Enable Weekly Pulse to receive personalized weekly insights, productivity analytics, upcoming task summaries, and progress tracking delivered directly to your email.'}
        </p>
      </div>
    </div>
  )
}

