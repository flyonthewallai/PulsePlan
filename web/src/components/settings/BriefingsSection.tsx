import { useState } from 'react'
import { Newspaper, Clock, Mail, Info, RefreshCw } from 'lucide-react'
import { cn } from '../../lib/utils'
import { typography, components } from '../../lib/design-tokens'
import { useSendTestBriefing } from '@/hooks/integrations'
import { ToggleSwitch } from './ToggleSwitch'

interface BriefingsSectionProps {
  isBriefingsEnabled: boolean
  setIsBriefingsEnabled: (value: boolean) => void
  scheduleContent: string
  setScheduleContent: (value: string) => void
  suggestionsContent: string
  setSuggestionsContent: (value: string) => void
  motivationContent: string
  setMotivationContent: (value: string) => void
  remindersContent: string
  setRemindersContent: (value: string) => void
}

export function BriefingsSection({
  isBriefingsEnabled,
  setIsBriefingsEnabled,
  scheduleContent,
  setScheduleContent,
  suggestionsContent,
  setSuggestionsContent,
  motivationContent,
  setMotivationContent,
  remindersContent,
  setRemindersContent,
}: BriefingsSectionProps) {
  const sendTestBriefingMutation = useSendTestBriefing()
  const [testBriefingStatus, setTestBriefingStatus] = useState<string | null>(null)

  const handleSendTestBriefing = async () => {
    try {
      setTestBriefingStatus('sending')
      const result = await sendTestBriefingMutation.mutateAsync({
        send_email: true,
        send_notification: false
      })
      if (result.success) {
        setTestBriefingStatus('success')
        setTimeout(() => setTestBriefingStatus(null), 5000)
      } else {
        setTestBriefingStatus('error')
        setTimeout(() => setTestBriefingStatus(null), 5000)
      }
    } catch (error) {
      console.error('Error sending test briefing:', error)
      setTestBriefingStatus('error')
      setTimeout(() => setTestBriefingStatus(null), 5000)
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-gray-400 text-sm">
        Customize your daily morning briefing to start each day informed and focused
      </p>

      <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-700/30">
          <div className="flex items-center gap-2">
            <Newspaper size={18} className="text-gray-400" />
            <span className="text-sm text-white font-medium">Daily Briefings Enabled</span>
          </div>
          <button
            onClick={() => setIsBriefingsEnabled(!isBriefingsEnabled)}
            className={cn(
              "w-10 h-5 rounded-full transition-colors",
              isBriefingsEnabled ? "bg-blue-500" : "bg-gray-600"
            )}
          >
            <div className={cn(
              "w-4 h-4 bg-white rounded-full transition-transform",
              isBriefingsEnabled ? "translate-x-5" : "translate-x-0.5"
            )} />
          </button>
        </div>

        <div className="flex items-center justify-between p-4 border-b border-gray-700/30">
          <div className="flex items-center gap-2">
            <Clock size={18} className="text-gray-400" />
            <span className="text-sm text-white font-medium">Delivery Time</span>
          </div>
          <span className="text-xs text-gray-400">7:00 AM</span>
        </div>

        <div className="p-4">
          <button
            onClick={handleSendTestBriefing}
            disabled={testBriefingStatus === 'sending'}
            className={cn(
              "w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors border",
              testBriefingStatus === 'sending'
                ? "bg-gray-600 text-gray-400 cursor-not-allowed border-gray-500"
                : testBriefingStatus === 'success'
                ? "bg-green-600 text-white border-green-500"
                : testBriefingStatus === 'error'
                ? "bg-red-600 text-white border-red-500"
                : "bg-white text-black hover:bg-gray-100 border-gray-300"
            )}
          >
            <Mail size={14} />
            {testBriefingStatus === 'sending' && (
              <>
                <RefreshCw size={14} className="animate-spin" />
                Sending Test Briefing...
              </>
            )}
            {testBriefingStatus === 'success' && 'Test Briefing Sent! Check Your Email'}
            {testBriefingStatus === 'error' && 'Failed to Send - Try Again'}
            {!testBriefingStatus && 'Send Test Briefing Now'}
          </button>
          <div className="flex items-center justify-center gap-1.5 text-xs text-gray-500 mt-2">
            <Info size={12} className="text-gray-400" aria-hidden="true" />
            <span>Get a preview of your daily briefing sent to your email right now</span>
          </div>
        </div>
      </div>

      {isBriefingsEnabled && (
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
          <div className="p-4 text-center border-b border-gray-700/50">
            <h3 className="text-sm font-semibold text-white mb-0.5">Good Morning there</h3>
            <p className="text-xs text-gray-400 italic">Here's your morning briefing</p>
          </div>
          
          <div className="p-4 space-y-3">
            <div>
              <h4 className={cn(typography.subsectionTitle, "mb-2")}>Schedule Overview</h4>
              <textarea
                value={scheduleContent}
                onChange={(e) => setScheduleContent(e.target.value)}
                className={cn(components.textarea.base, "w-full min-h-[50px]")}
                placeholder="Describe what you want to see in your schedule overview..."
              />
            </div>

            <div>
              <h4 className={cn(typography.subsectionTitle, "mb-2")}>Suggested Adjustments</h4>
              <textarea
                value={suggestionsContent}
                onChange={(e) => setSuggestionsContent(e.target.value)}
                className={cn(components.textarea.base, "w-full min-h-[50px]")}
                placeholder="Describe what AI suggestions you want to receive..."
              />
            </div>

            <div>
              <h4 className={cn(typography.subsectionTitle, "mb-2")}>Motivational Blurb</h4>
              <textarea
                value={motivationContent}
                onChange={(e) => setMotivationContent(e.target.value)}
                className={cn(components.textarea.base, "w-full min-h-[50px]")}
                placeholder="Describe what kind of motivation you want to receive..."
              />
            </div>

            <div>
              <h4 className={cn(typography.subsectionTitle, "mb-2")}>Important Reminders</h4>
              <textarea
                value={remindersContent}
                onChange={(e) => setRemindersContent(e.target.value)}
                className={cn(components.textarea.base, "w-full min-h-[50px]")}
                placeholder="Describe what reminders you want to see..."
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

