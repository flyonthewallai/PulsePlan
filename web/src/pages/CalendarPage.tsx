import { useState, useCallback } from 'react'
import { WeeklyCalendar } from '../features/calendar/WeeklyCalendar'
import { TaskModal } from '../features/tasks/TaskModal'
import { ArrowUp, Paperclip, Calendar } from 'lucide-react'
import type { Task } from '../types'

export function CalendarPage() {
  console.log('CalendarPage component rendering')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [showTaskModal, setShowTaskModal] = useState(false)
  const [newEventData, setNewEventData] = useState<{ start: string; end: string } | null>(null)
  const [messageText, setMessageText] = useState('')

  const handleEventClick = useCallback((task: Task) => {
    setSelectedTask(task)
    setShowTaskModal(true)
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

  const handleSendMessage = () => {
    if (messageText.trim() === '') return
    // TODO: Implement message sending
    console.log('Sending message:', messageText)
    setMessageText('')
  }

  return (
    <div className="min-h-screen bg-neutral-900 flex flex-col items-center">
      {/* Header with Greeting and Progress */}
      <div className="w-full max-w-7xl px-6 pt-24 pb-6">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">
            Your week
          </h1>
          <p className="text-base text-gray-400">
            {new Date().toLocaleDateString('en-US', { 
              weekday: 'long',
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>

        {/* AI Input Box */}
        <div className="bg-neutral-800/80 border border-gray-700/50 rounded-2xl p-3 mb-6 max-w-2xl mx-auto">
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Want me to move anything around?"
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              className="flex-1 bg-transparent text-white placeholder-gray-400 text-base focus:outline-none min-h-[38px]"
            />
          </div>
          <div className="flex justify-between items-center mt-1.5">
            <button className="p-1">
              <Paperclip size={16} className="text-gray-400 hover:text-gray-300 transition-colors" />
            </button>
            <button
              onClick={handleSendMessage}
              disabled={messageText.trim() === ''}
              className={`w-8 h-8 rounded-full flex items-center justify-center transition-all bg-white hover:bg-gray-100 ${
                messageText.trim() === ''
                  ? 'opacity-30 cursor-not-allowed'
                  : 'opacity-100'
              }`}
            >
              <ArrowUp size={16} className="text-black" />
            </button>
          </div>
        </div>

        {/* Compact Calendar Card */}
        <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
          <div className="flex items-center justify-between mb-4 px-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
              CALENDAR
            </span>
            <div className="w-4 h-4 flex items-center justify-center">
              <Calendar size={14} className="text-gray-400" />
            </div>
          </div>
          
          <WeeklyCalendar
            onEventClick={handleEventClick}
            onCreateEvent={handleCreateEvent}
          />
        </div>
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