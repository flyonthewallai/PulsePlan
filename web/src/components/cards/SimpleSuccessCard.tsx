import React from 'react'
import { Check, ListTodo, Calendar, Trash2, Edit, CheckSquare, X, Clock, Tag } from 'lucide-react'

interface SimpleSuccessCardProps {
  operation: string
  entityType: string
  entityTitle: string
  card: any
  acknowledgementMessage?: string
}

export function SimpleSuccessCard({ operation, entityType, entityTitle, card, acknowledgementMessage }: SimpleSuccessCardProps) {
  // Helper function to format date/time
  const formatDateTime = (dateStr: string) => {
    if (!dateStr) return null
    
    try {
      const date = new Date(dateStr)
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return null
      }
      
      const now = new Date()
      const diffMs = date.getTime() - now.getTime()
      const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))
      
      // Format time
      const timeStr = date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })
      
      // Format date with relative context
      if (diffDays === 0) {
        return `Today at ${timeStr}`
      } else if (diffDays === 1) {
        return `Tomorrow at ${timeStr}`
      } else if (diffDays === -1) {
        return `Yesterday at ${timeStr}`
      } else if (diffDays > 1 && diffDays <= 7) {
        return `${date.toLocaleDateString('en-US', { weekday: 'long' })} at ${timeStr}`
      } else {
        return `${date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        })}`
      }
    } catch (error) {
      return null
    }
  }

  // Helper function to render tags
  const renderTags = (tags: string[]) => {
    if (!tags || tags.length === 0) return null
    
    return (
      <div className="flex flex-wrap gap-1 mt-2">
        {tags.map((tag, index) => (
          <div
            key={index}
            className="flex items-center gap-1 bg-neutral-800 rounded-lg px-2 py-1"
          >
            <Tag size={10} className="text-gray-400" />
            <span className="text-xs text-white">{tag}</span>
          </div>
        ))}
      </div>
    )
  }
  const getIcon = () => {
    switch (entityType) {
      case 'task':
        return <CheckSquare size={12} className="text-neutral-800" />
      case 'event':
        return <Calendar size={12} className="text-neutral-800" />
      default:
        return <CheckSquare size={12} className="text-neutral-800" />
    }
  }

  const getOperationText = () => {
    switch (operation) {
      case 'created':
        return 'Added to to-dos'
      case 'updated':
        return 'Updated task'
      case 'deleted':
        return 'Removed from to-dos'
      case 'completed':
        return 'Completed task'
      default:
        return 'Success'
    }
  }

  const getStatusIcon = () => {
    switch (operation) {
      case 'created':
        return <Check size={16} className="text-green-500" strokeWidth={3} />
      case 'updated':
        return <Edit size={16} className="text-blue-500" strokeWidth={3} />
      case 'deleted':
        return <X size={16} className="text-red-500" strokeWidth={3} />
      case 'completed':
        return <Check size={16} className="text-green-500" strokeWidth={3} />
      default:
        return <Check size={16} className="text-green-500" strokeWidth={3} />
    }
  }

  const getStatusColor = () => {
    // Remove background colors - use clean icons like web search
    return ''
  }

  return (
    <div className="mb-6">
      {/* Success Card */}
      <div className="bg-neutral-900/80 border border-gray-700/50 rounded-xl p-4">
        {/* Task Title(s) with White Bullet Point(s) */}
        {(card?.details?.created_tasks && card.details.created_tasks.length > 1) || 
         (card?.details?.deleted_tasks && card.details.deleted_tasks.length > 1) ||
         (card?.details?.updated_tasks && card.details.updated_tasks.length > 1) ? (
          // Multiple tasks - show list
          <div className="space-y-2 mb-3">
            {(card?.details?.created_tasks || card?.details?.deleted_tasks || card?.details?.updated_tasks || []).map((taskName: string, index: number) => (
              <div key={index} className="flex items-center gap-3">
                <div className="w-2 h-2 bg-white rounded-full"></div>
                <h3 className={`text-white font-medium text-base leading-tight flex-1 ${
                  operation === 'deleted' ? 'line-through opacity-60' : ''
                }`}>
                  {taskName}
                </h3>
              </div>
            ))}
          </div>
        ) : (
          // Single task - show normally
          <div className="mb-3">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-white rounded-full"></div>
              <h3 className={`text-white font-medium text-base leading-tight flex-1 ${
                operation === 'deleted' ? 'line-through opacity-60' : ''
              }`}>
                {entityTitle}
              </h3>
            </div>
            
            {/* Date/Time and Tags for single task */}
            {operation === 'created' && card?.details && (
              <div className="ml-5 mt-2 space-y-2">
                {/* Due Date */}
                {card.details.due_date && (
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Clock size={14} />
                    <span>{formatDateTime(card.details.due_date)}</span>
                  </div>
                )}
                
                {/* Tags */}
                {renderTags(card.details.tags)}
              </div>
            )}
          </div>
        )}

        {/* Success Message with Status Icon and Entity Icon */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="text-sm text-gray-300">{getOperationText()}</span>
          </div>
          
          {/* Entity Type Icon */}
          <div className="w-5 h-5 bg-white rounded-full flex items-center justify-center">
            {getIcon()}
          </div>
        </div>
      </div>
    </div>
  )
}
