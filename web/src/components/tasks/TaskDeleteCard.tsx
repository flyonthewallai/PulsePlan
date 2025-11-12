import React from 'react'
import { Trash2, ListTodo } from 'lucide-react'
import type { Task } from '../../types'

interface TaskDeleteCardProps {
  task: Task
  onClose?: () => void
}

export function TaskDeleteCard({ task, onClose }: TaskDeleteCardProps) {
  return (
    <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4 mb-6">
      {/* Task Title with White Bullet Point */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-2 h-2 bg-white rounded-full"></div>
        <h3 className="text-white font-medium text-base leading-tight flex-1">
          {task.title}
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors text-lg leading-none"
          >
            ×
          </button>
        )}
      </div>

      {/* Success Message with Trash Icon and Todo Icon */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
            <Trash2 size={12} className="text-white" strokeWidth={3} />
          </div>
          <span className="text-sm text-gray-300">Removed from to-dos</span>
        </div>
        
        {/* Todo List Icon */}
        <ListTodo size={20} className="text-white" />
      </div>
    </div>
  )
}





