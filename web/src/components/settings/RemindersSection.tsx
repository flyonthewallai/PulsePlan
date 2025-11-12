import { Bell, Calendar, Mail, Smartphone } from 'lucide-react'
import { ToggleSwitch } from './ToggleSwitch'

interface RemindersSectionProps {
  isTaskRemindersEnabled: boolean
  setIsTaskRemindersEnabled: (value: boolean) => void
  isMissedSummaryEnabled: boolean
  setIsMissedSummaryEnabled: (value: boolean) => void
  isEmailEnabled: boolean
  setIsEmailEnabled: (value: boolean) => void
  isInAppEnabled: boolean
  setIsInAppEnabled: (value: boolean) => void
  isPushEnabled: boolean
  setIsPushEnabled: (value: boolean) => void
}

export function RemindersSection({
  isTaskRemindersEnabled,
  setIsTaskRemindersEnabled,
  isMissedSummaryEnabled,
  setIsMissedSummaryEnabled,
  isEmailEnabled,
  setIsEmailEnabled,
  isInAppEnabled,
  setIsInAppEnabled,
  isPushEnabled,
  setIsPushEnabled,
}: RemindersSectionProps) {
  return (
    <div className="space-y-6">
      <p className="text-gray-400 text-sm">Configure your notification preferences and delivery methods</p>

      <div>
        <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Task Reminders</h3>
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden divide-y divide-gray-700/40">
          <ToggleSwitch
            enabled={isTaskRemindersEnabled}
            onToggle={() => setIsTaskRemindersEnabled(!isTaskRemindersEnabled)}
            label="Task Reminders"
            description="Get notified before tasks are due"
            icon={<Bell size={18} className="text-gray-400" />}
          />
          <ToggleSwitch
            enabled={isMissedSummaryEnabled}
            onToggle={() => setIsMissedSummaryEnabled(!isMissedSummaryEnabled)}
            label="Missed Task Summary"
            description="Daily summary of incomplete tasks"
            icon={<Calendar size={18} className="text-gray-400" />}
          />
        </div>
      </div>

      <div>
        <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Delivery Methods</h3>
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden divide-y divide-gray-700/40">
          <ToggleSwitch
            enabled={isEmailEnabled}
            onToggle={() => setIsEmailEnabled(!isEmailEnabled)}
            label="Email"
            description="Receive notifications via email"
            icon={<Mail size={18} className="text-gray-400" />}
          />
          <ToggleSwitch
            enabled={isInAppEnabled}
            onToggle={() => setIsInAppEnabled(!isInAppEnabled)}
            label="In‑App"
            description="Show notifications within the app"
            icon={<Bell size={18} className="text-gray-400" />}
          />
          <ToggleSwitch
            enabled={isPushEnabled}
            onToggle={() => setIsPushEnabled(!isPushEnabled)}
            label="Push"
            description="Send push notifications to your device"
            icon={<Smartphone size={18} className="text-gray-400" />}
          />
        </div>
      </div>
    </div>
  )
}

