import { useState } from 'react'
import { ChevronDown, ChevronRight, ListTodo, Check } from 'lucide-react'

interface Task {
  id: string
  title: string
  status: string
  priority: string
  due_date?: string
  // Optional color sources
  color?: string
  courses?: {
    color?: string
  }
}

interface CollapsibleTaskListProps {
  tasks: Task[]
  taskCount: number
  onTaskToggle?: (taskId: string) => void
}

export function CollapsibleTaskList({ tasks, taskCount, onTaskToggle }: CollapsibleTaskListProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [localTasks, setLocalTasks] = useState(tasks)

  const handleTaskToggle = (taskId: string) => {
    setLocalTasks(prevTasks => 
      prevTasks.map(task => 
        task.id === taskId 
          ? { ...task, status: task.status === 'completed' ? 'pending' : 'completed' }
          : task
      )
    )
    onTaskToggle?.(taskId)
  }

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high': return '#FF5757'
      case 'medium': return '#FFC043'
      case 'low': return '#4CD964'
      default: return '#8E6FFF'
    }
  }

  const getTaskDisplayColor = (task: Task) => {
    return task.courses?.color || task.color || getPriorityColor(task.priority)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today'
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow'
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
    }
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  return (
    <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl mb-6">
      {/* Collapsible Header */}
      <div 
        className="group p-4 cursor-pointer hover:bg-neutral-800/60 transition-colors duration-200 rounded-xl"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 bg-white rounded-full flex items-center justify-center">
              <ListTodo size={12} className="text-neutral-800" />
            </div>
            <span className="text-white font-medium text-base">
              Tasks ({taskCount})
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
           <div 
             className="space-y-2 max-h-96 overflow-y-auto"
             style={{
               scrollbarWidth: 'thin',
               scrollbarColor: 'rgba(75, 85, 99, 0.5) transparent'
             }}
           >
            {localTasks.map((task, index) => (
              <div 
                key={task.id || index} 
                className="flex items-start gap-3 p-4 rounded-xl transition-colors duration-150"
                style={{ backgroundColor: '#2a2a2a' }}
              >
                 {/* Circular checkbox with course color fallback to priority */}
                 <button
                   className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                     task.status === 'completed'
                       ? 'bg-green-500 border-green-500' 
                       : `border-2 hover:border-opacity-80`
                   }`}
                   style={{
                     backgroundColor: task.status === 'completed' ? '#10B981' : 'transparent',
                    borderColor: task.status === 'completed' ? '#10B981' : getTaskDisplayColor(task)
                   }}
                   onClick={() => handleTaskToggle(task.id)}
                 >
                   {task.status === 'completed' && (
                     <Check size={12} className="text-white" strokeWidth={3} />
                   )}
                 </button>
                
                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium leading-tight ${
                    task.status === 'completed' 
                      ? 'line-through text-gray-400' 
                      : 'text-white'
                  }`}>
                    {task.title}
                  </div>
                  
                   {task.due_date && (
                     <div className="text-xs font-medium text-gray-400 mt-1">
                       {formatDate(task.due_date)} • {formatTime(task.due_date)}
                     </div>
                   )}
                </div>
              </div>
            ))}
          </div>
         </div>
       )}
     </div>
   )
 }
