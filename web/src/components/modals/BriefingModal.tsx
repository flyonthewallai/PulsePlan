import { useMemo } from 'react'
import { X, Mail, Calendar, CheckSquare, Star, Lightbulb, Loader2, Newspaper } from 'lucide-react'
import { useTodaysBriefing } from '@/hooks/integrations'

interface BriefingContent {
  greeting: string
  email_summary: string
  calendar_overview: string
  task_status: string
  priority_items: string[]
  recommendations: string[]
  closing: string
}

interface BriefingModalProps {
  isOpen: boolean
  onClose: () => void
}

export function BriefingModal({ isOpen, onClose }: BriefingModalProps) {
  const { data: briefingData, isLoading, error } = useTodaysBriefing()

  // Extract the synthesized content from the briefing data
  const briefing = useMemo<BriefingContent | null>(() => {
    if (!briefingData) return null

    // Navigate through the nested structure
    const content = briefingData.content?.briefing?.content_sections?.synthesized_content ||
                   briefingData.content?.raw_result?.result?.briefing?.content_sections?.synthesized_content

    if (!content) return null

    return {
      greeting: content.greeting || "Here's your daily briefing.",
      email_summary: content.email_summary || 'No email updates available.',
      calendar_overview: content.calendar_overview || 'No events scheduled.',
      task_status: content.task_status || 'No tasks.',
      priority_items: content.priority_items || [],
      recommendations: content.recommendations || [],
      closing: content.closing || 'Have a productive day!'
    }
  }, [briefingData])

  const handleBackdrop = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div
      className={`fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300 cursor-default ${
        isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}
      onClick={handleBackdrop}
    >
      <div
        className={`border border-gray-700/50 w-full max-w-3xl rounded-xl h-[75vh] flex flex-col cursor-default transition-all duration-300 shadow-2xl ${
          isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        style={{ backgroundColor: '#121212' }}
        onClick={(e) => e.stopPropagation()}
      >
        {isOpen ? (
          <>
            {/* Header - Matching Card Style */}
            <div className="p-5 border-b border-gray-700/30">
          {/* Title Row */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Newspaper size={16} className="text-white" />
              </div>
              <h2 className="text-lg font-semibold text-white tracking-tight">
                Daily Briefing
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-neutral-800/60"
              aria-label="Close modal"
              type="button"
            >
              <X size={18} />
            </button>
          </div>

          {/* Date - Clean Inline */}
          <div className="text-sm text-gray-400 font-medium">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              month: 'long',
              day: 'numeric',
              year: 'numeric'
            })}
          </div>
        </div>

        {/* Content */}
        <div
          className="flex-1 overflow-y-auto px-5 py-4"
          style={{
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(75, 85, 99, 0.3) transparent'
          }}
        >
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-6 h-6 text-blue-500 animate-spin mb-3" />
              <p className="text-sm text-gray-400">Loading your briefing...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center mb-3">
                <X className="w-5 h-5 text-red-400" />
              </div>
              <p className="text-sm font-medium text-gray-400 mb-1">No briefing available</p>
              <p className="text-xs text-gray-500">Try generating a new briefing</p>
            </div>
          ) : briefing ? (
            <div className="space-y-5">
              {/* Greeting */}
              <div className="text-base text-gray-200 font-medium">
                {briefing.greeting}
              </div>

              {/* Email Summary */}
              <div className="p-3.5 rounded-lg bg-neutral-900/30 border border-gray-700/30">
                <div className="flex items-center gap-2.5 mb-2.5">
                  <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <Mail className="w-3.5 h-3.5 text-blue-400" />
                  </div>
                  <h3 className="text-xs font-semibold text-white uppercase tracking-wider">Email Summary</h3>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {briefing.email_summary}
                </p>
              </div>

              {/* Calendar Overview */}
              <div className="p-3.5 rounded-lg bg-neutral-900/30 border border-gray-700/30">
                <div className="flex items-center gap-2.5 mb-2.5">
                  <div className="w-7 h-7 rounded-lg bg-purple-500/10 flex items-center justify-center">
                    <Calendar className="w-3.5 h-3.5 text-purple-400" />
                  </div>
                  <h3 className="text-xs font-semibold text-white uppercase tracking-wider">Calendar Overview</h3>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {briefing.calendar_overview}
                </p>
              </div>

              {/* Task Status */}
              <div className="p-3.5 rounded-lg bg-neutral-900/30 border border-gray-700/30">
                <div className="flex items-center gap-2.5 mb-2.5">
                  <div className="w-7 h-7 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <CheckSquare className="w-3.5 h-3.5 text-green-400" />
                  </div>
                  <h3 className="text-xs font-semibold text-white uppercase tracking-wider">Task Status</h3>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {briefing.task_status}
                </p>
              </div>

              {/* Priority Items */}
              {briefing.priority_items && briefing.priority_items.length > 0 && (
                <div className="p-3.5 rounded-lg bg-neutral-900/30 border border-gray-700/30">
                  <div className="flex items-center gap-2.5 mb-2.5">
                    <div className="w-7 h-7 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                      <Star className="w-3.5 h-3.5 text-yellow-400" />
                    </div>
                    <h3 className="text-xs font-semibold text-white uppercase tracking-wider">Priority Items</h3>
                  </div>
                  <ul className="space-y-2">
                    {briefing.priority_items.map((item, index) => (
                      <li key={index} className="flex items-start gap-2.5 text-gray-300 text-sm">
                        <span className="text-yellow-400 mt-0.5 text-xs">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommendations */}
              {briefing.recommendations && briefing.recommendations.length > 0 && (
                <div className="p-3.5 rounded-lg bg-neutral-900/30 border border-gray-700/30">
                  <div className="flex items-center gap-2.5 mb-2.5">
                    <div className="w-7 h-7 rounded-lg bg-orange-500/10 flex items-center justify-center">
                      <Lightbulb className="w-3.5 h-3.5 text-orange-400" />
                    </div>
                    <h3 className="text-xs font-semibold text-white uppercase tracking-wider">Recommendations</h3>
                  </div>
                  <ul className="space-y-2">
                    {briefing.recommendations.map((item, index) => (
                      <li key={index} className="flex items-start gap-2.5 text-gray-300 text-sm">
                        <span className="text-orange-400 mt-0.5 text-xs">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Closing */}
              <div className="pt-3 border-t border-gray-700/30">
                <p className="text-gray-300 text-sm font-medium text-center">
                  {briefing.closing}
                </p>
              </div>
            </div>
          ) : null}
        </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
