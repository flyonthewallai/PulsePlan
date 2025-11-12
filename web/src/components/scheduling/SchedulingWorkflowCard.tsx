import React, { useState } from 'react'
import { ChevronDown, ChevronRight, Calendar, Sparkles, Check, Clock } from 'lucide-react'

interface TimeBlock {
  title: string
  start_time: string
  end_time: string
  duration?: number
  type?: string
}

interface ScheduleData {
  schedule?: TimeBlock[]
  commit_info?: {
    blocks_committed: number
    status: string
  }
  message?: string
  status?: string
}

interface SchedulingWorkflowCardProps {
  scheduleData?: ScheduleData
  onClose?: () => void
}

export function SchedulingWorkflowCard({ scheduleData, onClose }: SchedulingWorkflowCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const isCompleted = scheduleData?.status === 'completed'
  const blocksCount = scheduleData?.commit_info?.blocks_committed || scheduleData?.schedule?.length || 0

  return (
    <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl mb-6">
      {/* Collapsible Header */}
      <div
        className="group p-4 cursor-pointer hover:bg-neutral-800/60 transition-colors duration-200 rounded-xl"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              {isCompleted ? (
                <Check size={16} className="text-green-500" strokeWidth={3} />
              ) : (
                <>
                  {/* Animated schedule icon */}
                  <div className="relative w-5 h-5">
                    <Calendar size={20} className="text-blue-400 animate-pulse" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-3 h-3 bg-blue-400/30 rounded-full animate-ping" />
                    </div>
                  </div>
                  {/* Sparkles for extra effect */}
                  <Sparkles size={16} className="text-blue-300 animate-pulse" />
                </>
              )}
            </div>
            <span className="text-white font-medium text-base">
              {isCompleted
                ? `Schedule created: ${blocksCount} time block${blocksCount !== 1 ? 's' : ''}`
                : 'Creating your schedule...'
              }
            </span>
          </div>
          <div className="text-gray-400 transition-all duration-200 group-hover:text-white">
            {isExpanded ? (
              <ChevronDown size={20} />
            ) : (
              <ChevronRight size={20} />
            )}
          </div>
        </div>
      </div>

      {/* Collapsible Content */}
      {isExpanded && (
        <div className="px-4 pb-4">
          {!isCompleted ? (
            <>
              {/* Status - In Progress */}
              <div className="flex items-center gap-2 mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                  <span className="text-sm text-gray-300">Analyzing your tasks and calendar...</span>
                </div>
              </div>

              {/* Progress indicator */}
              <div className="space-y-3">
                <div className="bg-neutral-700/50 rounded-lg p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="h-1.5 bg-neutral-600 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-400 rounded-full animate-progress-bar"
                             style={{
                               animation: 'progress 2s ease-in-out infinite'
                             }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Status - Completed */}
              <div className="flex items-center gap-2 mb-4">
                <Check size={20} className="text-green-500" strokeWidth={3} />
                <span className="text-sm text-gray-300">Schedule created successfully</span>
              </div>

              {/* Message */}
              {scheduleData?.message && (
                <div className="mb-4 text-sm text-gray-300">
                  {scheduleData.message}
                </div>
              )}

              {/* Scheduled blocks */}
              {scheduleData?.schedule && scheduleData.schedule.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-white font-medium text-sm mb-2">
                    Scheduled Time Blocks ({blocksCount})
                  </h4>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {scheduleData.schedule.map((block, index) => {
                      const startTime = new Date(block.start_time).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })
                      const endTime = new Date(block.end_time).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })

                      return (
                        <div
                          key={index}
                          className="p-3 bg-neutral-700/50 rounded-lg hover:bg-neutral-700/60 transition-colors duration-150"
                        >
                          <div className="flex items-start gap-3">
                            <Clock size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <div className="text-white font-medium text-sm mb-1">
                                {block.title}
                              </div>
                              <div className="text-xs text-gray-400">
                                {startTime} - {endTime}
                                {block.duration && ` (${block.duration} min)`}
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      <style>{`
        @keyframes progress {
          0% {
            width: 0%;
          }
          50% {
            width: 70%;
          }
          100% {
            width: 0%;
          }
        }

        .animate-progress-bar {
          animation: progress 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}
