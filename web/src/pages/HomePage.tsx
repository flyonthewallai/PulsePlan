import { useState, useMemo } from 'react'
import { usePageTitle } from '../hooks/usePageTitle'
import { useNavigate } from 'react-router-dom'
import { getGreeting } from '../lib/utils'
import { Bell, Calendar, Newspaper, Mail, Timer, Plus, History, CheckSquare, Star, Loader2 } from 'lucide-react'
import { TasksCard } from '../components/TasksCard'
import { SimpleTodosCard } from '../components/SimpleTodosCard'
import { UpcomingCalendarCard } from '../components/UpcomingCalendarCard'
import { UpcomingExamsCard } from '../components/UpcomingExamsCard'
import { BriefingModal } from '../components/BriefingModal'
import { CommandInput } from '../components/CommandInput'
import { useTasks } from '../hooks/useTasks'
import { useTaskUpdates } from '../hooks/useTaskUpdates'
import { useProfile } from '../hooks/useProfile'
import { useTodaysBriefing } from '../hooks/useBriefing'

export function HomePage() {
  usePageTitle('Home')
  const navigate = useNavigate()
  const [messageText, setMessageText] = useState('')
  const [showBriefing, setShowBriefing] = useState(false)

  // Enable real-time task updates
  useTaskUpdates()

  // Use React Query for caching and data fetching
  useTasks()

  // Profile for greeting personalization
  const { data: profile } = useProfile()
  const displayName = profile?.full_name?.split(' ')[0] || 'there'

  // Fetch briefing data
  const { data: briefingData, isLoading: briefingLoading } = useTodaysBriefing()

  // Extract briefing snapshot
  const briefingSnapshot = useMemo(() => {
    if (!briefingData) return null

    const content = (briefingData.content as any)?.briefing?.content_sections?.synthesized_content ||
                   (briefingData.content as any)?.raw_result?.result?.briefing?.content_sections?.synthesized_content

    if (!content) return null

    return {
      taskStatus: content.task_status || 'No tasks available',
      priorityCount: content.priority_items?.length || 0,
      calendarPreview: content.calendar_overview || 'No events scheduled'
    }
  }, [briefingData])

  const handleSendMessage = async () => {
    const trimmed = messageText.trim()
    if (!trimmed) return

    // Navigate to chat page with the message
    // The chat page will handle both commands and regular messages
    navigate(`/chat?message=${encodeURIComponent(trimmed)}`)
    setMessageText('')
  }

  return (
    <div className="min-h-screen flex flex-col items-center relative" style={{ backgroundColor: '#0f0f0f' }}>
      

      <button
        type="button"
        className="fixed top-4 px-3 py-2 rounded-lg hover:bg-neutral-800/20 transition-colors z-50 group flex items-center gap-2"
        style={{ left: 'calc(var(--sidebar-width, 4rem) + 1rem)' }}
        aria-label="Past Chats"
        onClick={() => navigate('/chat')}
      >
        <History size={16} className="text-gray-400 group-hover:text-white transition-colors" />
        <span className="text-gray-400 group-hover:text-white transition-colors text-sm font-medium">Past Chats</span>
      </button>

      <button
        type="button"
        className="fixed top-4 right-4 p-2 rounded-lg hover:bg-neutral-800/20 transition-colors z-50 group" 
        aria-label="Notifications"
      >
        <Bell size={18} className="text-gray-400 group-hover:text-white transition-colors" />
      </button>

      {/* Main content container */}
      <div className="w-full max-w-4xl px-6 pt-24 pb-6">
        {/* Greeting */}
        <div className="text-center mb-4">
          <h1 className="text-2xl font-bold text-white mb-2">{getGreeting()}, {displayName}</h1>
          <p className="text-base text-gray-400">
            {new Date().toLocaleDateString('en-US', { 
              weekday: 'long',
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>

        {/* Agent textbox with command support */}
        <CommandInput
          value={messageText}
          onChange={setMessageText}
          onSubmit={handleSendMessage}
          placeholder="How can I help you today?"
          className="mb-6"
        />

        {/* Quick Actions - smaller to fit more */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-6">
          <button className="flex items-center justify-between bg-neutral-800/40 border border-gray-700/50 rounded-xl p-3 hover:border-gray-500/70 hover:ring-1 hover:ring-gray-500/30 transition-all">
            <span className="text-gray-200 text-sm font-medium">Create Schedule</span>
            <Calendar size={16} className="text-gray-400" />
          </button>
          <button className="flex items-center justify-between bg-neutral-800/40 border border-gray-700/50 rounded-xl p-3 hover:border-gray-500/70 hover:ring-1 hover:ring-gray-500/30 transition-all">
            <span className="text-gray-200 text-sm font-medium">Summarize Emails</span>
            <Mail size={16} className="text-gray-400" />
          </button>
          <button className="flex items-center justify-between bg-neutral-800/40 border border-gray-700/50 rounded-xl p-3 hover:border-gray-500/70 hover:ring-1 hover:ring-gray-500/30 transition-all" onClick={() => navigate('/pomodoro')}>
            <span className="text-gray-200 text-sm font-medium">Start Pomodoro</span>
            <Timer size={16} className="text-gray-400" />
          </button>
          <button className="flex items-center justify-between bg-neutral-800/40 border border-gray-700/50 rounded-xl p-3 hover:border-gray-500/70 hover:ring-1 hover:ring-gray-500/30 transition-all">
            <span className="text-gray-200 text-sm font-medium">Add To-do</span>
            <Plus size={16} className="text-gray-400" />
          </button>
        </div>

        {/* Task Lists */}
        <div className="space-y-4">
          {/* Briefing and Upcoming cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Briefing Card */}
            <button
              onClick={() => setShowBriefing(true)}
              className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-5 h-full flex flex-col hover:border-gray-600/50 hover:bg-neutral-800/60 transition-all text-left group"
            >
              <div className="flex items-center justify-between mb-4 px-1">
                <span className="text-xs font-semibold tracking-wider uppercase text-gray-400 group-hover:text-gray-300 transition-colors">
                  BRIEFING
                </span>
                <div className="w-4 h-4 flex items-center justify-center">
                  <Newspaper size={16} className="text-gray-400 group-hover:text-gray-300 transition-colors" />
                </div>
              </div>

              {briefingLoading ? (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <Loader2 size={16} className="text-gray-400 animate-spin mx-auto mb-2" />
                    <div className="text-xs text-gray-500">Loading briefing...</div>
                  </div>
                </div>
              ) : briefingSnapshot ? (
                <div className="space-y-3 flex-1">
                  {/* Priority Items Count */}
                  {briefingSnapshot.priorityCount > 0 && (
                    <div className="flex items-center gap-3">
                      <Star size={16} className="text-blue-500 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-white">
                          {briefingSnapshot.priorityCount} Priority {briefingSnapshot.priorityCount === 1 ? 'Item' : 'Items'}
                        </div>
                        <div className="text-xs text-gray-400">Needs your attention</div>
                      </div>
                    </div>
                  )}

                  {/* Task Status */}
                  <div className="flex items-center gap-3">
                    <CheckSquare size={16} className="text-gray-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-gray-300 line-clamp-2">
                        {briefingSnapshot.taskStatus}
                      </div>
                    </div>
                  </div>

                  {/* Calendar Preview */}
                  <div className="flex items-center gap-3">
                    <Calendar size={16} className="text-gray-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-gray-300 line-clamp-2">
                        {briefingSnapshot.calendarPreview}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col justify-center">
                  <div className="text-sm text-gray-400 text-center">
                    No briefing available
                  </div>
                  <div className="text-xs text-gray-500 text-center mt-1">
                    Generate your daily briefing
                  </div>
                </div>
              )}
            </button>

          {/* Upcoming Exams Card */}
          <UpcomingExamsCard />
          </div>

          {/* Assignments and Todos side by side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TasksCard />
          <SimpleTodosCard />
        </div>

          {/* Calendar card below */}
        <UpcomingCalendarCard />
        </div>
      </div>

      {/* Briefing Modal */}
      <BriefingModal isOpen={showBriefing} onClose={() => setShowBriefing(false)} />
    </div>
  )
}