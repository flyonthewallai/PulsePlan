import React, { useState } from 'react'
import { Check, ListTodo, Search, Loader2, ChevronDown, ChevronRight, ExternalLink, Globe } from 'lucide-react'
import type { Task } from '@/types'
import { CollapsibleSearchResults } from '../ui/common'

interface TaskSuccessCardProps {
  task: Task
  onClose?: () => void
}

export function TaskSuccessCard({ task, onClose }: TaskSuccessCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  // Check if this is a search task
  const isSearchTask = task.workflow_type === 'search'
  const isCompleted = task.status === 'completed'
  const hasSearchData = task.result?.search_data
  
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
              {/* Status indicator for search tasks */}
              {isSearchTask && (
                <>
                  {isCompleted ? (
                    <Check size={16} className="text-green-500" strokeWidth={3} />
                  ) : (
                    <Loader2 size={16} className="text-white animate-spin" />
                  )}
                </>
              )}
              {/* Globe icon */}
              <div className="w-5 h-5 bg-white rounded-full flex items-center justify-center">
                <Globe size={12} className="text-neutral-800" />
              </div>
            </div>
            <span className="text-white font-medium text-base">
              {isSearchTask 
                ? `Web search: ${task.result?.search_data?.query || task.description?.replace(/^I'll search for '(.+)' for you\.$/, '$1') || 'search query'}`
                : task.title
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
          {/* Status and Actions */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              {isSearchTask ? (
                <>
                  {!isCompleted && (
                    <>
                      <Loader2 size={20} className="text-white animate-spin" />
                      <span className="text-sm text-gray-300">Searching...</span>
                    </>
                  )}
                </>
              ) : (
                <>
                  <Check size={20} className="text-green-500" strokeWidth={3} />
                  <span className="text-sm text-gray-300">Added to to-dos</span>
                </>
              )}
            </div>
          </div>

          {/* Search Sources (if completed and has data) */}
          {isSearchTask && isCompleted && hasSearchData && (
            <div className="space-y-3">
              <h4 className="text-white font-medium text-sm mb-2">Sources ({hasSearchData.total_results})</h4>
              <div 
                className="space-y-3 max-h-96 overflow-y-auto"
                style={{
                  scrollbarWidth: 'thin',
                  scrollbarColor: 'rgba(75, 85, 99, 0.5) transparent'
                }}
              >
                {hasSearchData.results.map((result, index) => (
                  <div 
                    key={index}
                    className="p-3 bg-neutral-700/50 rounded-lg hover:bg-neutral-700/60 transition-colors duration-150"
                  >
                    <div className="flex items-start gap-3">
                      {/* Favicon or default icon */}
                      <div className="w-4 h-4 mt-1 flex-shrink-0">
                        {result.favicon ? (
                          <img 
                            src={result.favicon} 
                            alt="" 
                            className="w-4 h-4 rounded-sm"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none'
                            }}
                          />
                        ) : (
                          <div className="w-4 h-4 bg-gray-500 rounded-sm"></div>
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        {/* Title */}
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <a 
                            href={result.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-white font-medium text-sm leading-tight hover:text-blue-300 transition-colors cursor-pointer"
                          >
                            {result.title}
                          </a>
                          <a 
                            href={result.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-gray-400 hover:text-blue-300 transition-colors"
                          >
                            <ExternalLink size={12} className="flex-shrink-0 mt-0.5" />
                          </a>
                        </div>

                        {/* URL */}
                        <div className="text-xs text-gray-400 mb-2">
                          {result.url}
                          {result.published_date && (
                            <span className="ml-2">• {new Date(result.published_date).toLocaleDateString()}</span>
                          )}
                        </div>

                        {/* Content snippet */}
                        <div className="text-xs text-gray-300 leading-relaxed line-clamp-3">
                          {result.content}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

