import React from 'react'
import { TaskSuccessCard } from '../components/TaskSuccessCard'
import { TaskDeleteCard } from '../components/TaskDeleteCard'
import { useTaskSuccess } from '../contexts/TaskSuccessContext'

export function TaskSuccessOverlay() {
  const { 
    showSuccessCard, 
    successTask, 
    hideTaskSuccess,
    showDeleteCard,
    deletedTask,
    hideTaskDelete
  } = useTaskSuccess()

  return (
    <>
      {/* Task Creation Success Card */}
      {showSuccessCard && successTask && (
        <div className="fixed top-4 right-4 z-50 max-w-sm">
          <TaskSuccessCard
            task={successTask}
            onClose={hideTaskSuccess}
          />
        </div>
      )}

      {/* Task Deletion Success Card */}
      {showDeleteCard && deletedTask && (
        <div className="fixed top-4 right-4 z-50 max-w-sm">
          <TaskDeleteCard
            task={deletedTask}
            onClose={hideTaskDelete}
          />
        </div>
      )}
    </>
  )
}

