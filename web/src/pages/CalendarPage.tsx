import { useState, useCallback } from 'react'
import { WeeklyCalendar } from '../features/calendar/WeeklyCalendar'
import { TaskModal } from '../features/tasks/TaskModal'
import type { Task, CalendarEvent } from '../types'

export function CalendarPage() {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [showTaskModal, setShowTaskModal] = useState(false)
  const [newEventData, setNewEventData] = useState<{ start: string; end: string } | null>(null)

  const handleEventClick = useCallback((event: CalendarEvent) => {
    // If the event has an associated task, set it for the modal
    if (event.task) {
      setSelectedTask(event.task)
      setShowTaskModal(true)
    }
  }, [])

  const handleCreateEvent = useCallback((eventData: { start: string; end: string }) => {
    setNewEventData(eventData)
    setSelectedTask(null)
    setShowTaskModal(true)
  }, [])

  const handleCloseModal = () => {
    setShowTaskModal(false)
    setSelectedTask(null)
    setNewEventData(null)
  }

  return (
    <div className="min-h-screen bg-neutral-900 flex justify-center">
      {/* Centered calendar container */}
      <div className="w-full max-w-7xl px-8 pt-20 pb-8">
        <WeeklyCalendar
          onEventClick={handleEventClick}
          onCreateEvent={handleCreateEvent}
          className="minimal-calendar"
        />
      </div>

      {/* Task Modal */}
      {showTaskModal && (
        <TaskModal
          task={selectedTask}
          initialData={newEventData}
          onClose={handleCloseModal}
        />
      )}
    </div>
  )
}