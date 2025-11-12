import React, { useState } from 'react'
import { CheckCircle2, Clock, CheckCheck, Check, BarChart3, Loader2, AlertCircle } from 'lucide-react'
import { PulseTrace } from '../ui/common'
import { useTodaysBriefing } from '@/hooks/integrations'

export function DailySummaryCard() {
  const [showMessage, setShowMessage] = useState(true)
  const { data: briefing, isLoading, error } = useTodaysBriefing()

  // Extract briefing content with fallbacks
  const content = briefing?.content || {}
  const summary = content.summary || content.greeting || 'Your daily briefing is ready!'
  const tasksCount = content.tasks_count || content.tasks?.length || 0
  const deadlinesCount = content.deadlines_count || content.upcoming_deadlines?.length || 0

  // Show loading state
  if (isLoading) {
    return (
      <div className="mb-5">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
            DAILY SUMMARY
          </span>
          <BarChart3 size={16} className="text-gray-400" />
        </div>

        <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="w-8 h-8 bg-gray-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <Loader2 size={16} className="text-gray-400 animate-spin" />
              </div>
              <div className="text-sm font-medium text-gray-400 mb-1">
                Loading your briefing...
              </div>
              <div className="text-xs text-gray-400">
                Please wait
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="mb-5">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
            DAILY SUMMARY
          </span>
          <BarChart3 size={16} className="text-gray-400" />
        </div>

        <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <AlertCircle size={20} className="text-red-400" />
            <span className="text-sm font-medium text-red-400">Failed to load briefing</span>
          </div>
        </div>
      </div>
    )
  }

  // Compact view (message dismissed)
  if (!showMessage) {
    return (
      <div className="mb-5">
        {/* Overview Section Header */}
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
            OVERVIEW
          </span>
          <BarChart3 size={16} className="text-gray-400" />
        </div>

        <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
          <div className="flex items-center">
            <div className="flex items-center gap-3">
              <CheckCircle2 size={20} className="text-white opacity-90" />
              <span className="text-sm font-medium text-white">
                {tasksCount} {tasksCount === 1 ? 'Task' : 'Tasks'} Today
              </span>
            </div>
          </div>
          <div className="flex items-center mt-3">
            <div className="flex items-center gap-3">
              <Clock size={20} className="text-white opacity-90" />
              <span className="text-sm font-medium text-white">
                {deadlinesCount} {deadlinesCount === 1 ? 'Deadline' : 'Deadlines'}
              </span>
            </div>
          </div>
          <div className="flex items-center mt-3">
            <div className="flex items-center gap-3">
              <CheckCheck size={20} className="text-white opacity-90" />
              <span className="text-sm font-medium text-white">All on track</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Full view with AI message
  return (
    <div className="mb-5">
      <div className="flex items-start gap-3 mb-6">
        <div className="w-8 h-8 flex items-center justify-center">
          <PulseTrace active={false} width={24} height={24} />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <button
              className="p-1 -mr-1"
              onClick={() => setShowMessage(false)}
            >
              <Check size={18} className="text-gray-400" />
            </button>
          </div>
          <p className="text-lg leading-relaxed text-white">
            {summary}
          </p>
        </div>
      </div>

      {/* Overview Section Header */}
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
          OVERVIEW
        </span>
        <BarChart3 size={16} className="text-gray-400" />
      </div>

      <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
        <div className="flex items-center">
          <div className="flex items-center gap-3">
            <CheckCircle2 size={20} className="text-white opacity-90" />
            <span className="text-sm font-medium text-white">
              {tasksCount} {tasksCount === 1 ? 'Task' : 'Tasks'} Today
            </span>
          </div>
        </div>
        <div className="flex items-center mt-3">
          <div className="flex items-center gap-3">
            <Clock size={20} className="text-white opacity-90" />
            <span className="text-sm font-medium text-white">
              {deadlinesCount} Upcoming {deadlinesCount === 1 ? 'Deadline' : 'Deadlines'}
            </span>
          </div>
        </div>
        <div className="flex items-center mt-3">
          <div className="flex items-center gap-3">
            <CheckCheck size={20} className="text-white opacity-90" />
            <span className="text-sm font-medium text-white">All on track</span>
          </div>
        </div>
      </div>
    </div>
  )
}
