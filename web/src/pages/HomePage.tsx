import { useState } from 'react'
import { getGreeting } from '../lib/utils'
import { Paperclip, ArrowUp, X, Clock, Target, Zap, Calendar, CheckCircle, AlertCircle, PlayCircle, BarChart3, Bell, MessageSquare, Newspaper } from 'lucide-react'
import { TasksCard } from '../components/TasksCard'
import { SimpleTodosCard } from '../components/SimpleTodosCard'
import { UpcomingCalendarCard } from '../components/UpcomingCalendarCard'
import { ChatPage } from './ChatPage'
import { useTasks } from '../hooks/useTasks'
import { useTaskUpdates } from '../hooks/useTaskUpdates'

export function HomePage() {
  const [messageText, setMessageText] = useState('')
  const [showChat, setShowChat] = useState(false)
  const [initialChatMessage, setInitialChatMessage] = useState('')
  const [showOverviewModal, setShowOverviewModal] = useState(false)

  // Enable real-time task updates
  useTaskUpdates()
  
  // Use React Query for caching and data fetching
  const { data: allTasks = [] } = useTasks()

  // Calculate real stats
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  
  const todaysTasks = allTasks.filter(task => {
    const taskDate = new Date(task.due_date)
    return taskDate >= today && taskDate < tomorrow
  })
  
  const completedTasks = allTasks.filter(task => task.status === 'completed')
  const pendingTasks = allTasks.filter(task => task.status === 'pending')
  const inProgressTasks = allTasks.filter(task => task.status === 'in_progress')
  
  const totalEstimatedMinutes = allTasks.reduce((total, task) => {
    return total + (task.estimated_minutes || 60)
  }, 0)
  
  const hoursEstimate = Math.round(totalEstimatedMinutes / 60 * 10) / 10 // Round to 1 decimal
  
  const todaysEstimatedMinutes = todaysTasks.reduce((total, task) => {
    return total + (task.estimated_minutes || 60)
  }, 0)
  
  const todaysHoursEstimate = Math.round(todaysEstimatedMinutes / 60 * 10) / 10

  const handleSendMessage = () => {
    if (messageText.trim() === '') return
    setInitialChatMessage(messageText)
    setShowChat(true)
    setMessageText('')
  }

  const handleBackToHome = () => {
    setShowChat(false)
    setInitialChatMessage('')
  }

  // Show chat page if a message was sent
  if (showChat) {
    return <ChatPage initialMessage={initialChatMessage} onBack={handleBackToHome} />
  }

  return (
    <div className="min-h-screen bg-neutral-900 flex flex-col items-center relative">
      {/* Corner controls */}
      <button
        type="button"
        className="absolute top-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-neutral-800/80 border border-gray-700/50 text-gray-300 hover:text-white hover:bg-neutral-800 transition-colors z-40 group"
        style={{ left: 'var(--sidebar-width, 1rem)' }}
      >
        <MessageSquare size={16} className="text-gray-400 group-hover:text-white transition-colors" />
        <span className="text-sm font-medium">Past Chats</span>
      </button>

      <button
        type="button"
        className="fixed top-4 right-4 p-2 rounded-lg bg-neutral-800/80 border border-gray-700/50 hover:bg-neutral-800 transition-colors z-50 group"
        aria-label="Notifications"
      >
        <Bell size={18} className="text-gray-400 group-hover:text-white transition-colors" />
      </button>

      {/* Header with Greeting and Progress */}
      <div className="w-full max-w-4xl px-6 pt-24 pb-6">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">
            {getGreeting()}, <span className="text-white">Conner</span>
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
              placeholder="How can I help you today?"
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

        {/* 2x2 Grid for Overview Cards */}
        <div className="grid grid-cols-2 gap-4 max-w-4xl mx-auto mb-4">
          {/* Daily Briefing Card */}
          <div 
            className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4 cursor-pointer hover:bg-neutral-800 transition-colors"
            onClick={() => setShowOverviewModal(true)}
          >
            <div className="flex items-center justify-between mb-3 px-1">
              <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
                DAILY BRIEFING
              </span>
              <div className="w-4 h-4 flex items-center justify-center">
                <Newspaper size={16} className="text-gray-400" />
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-white leading-relaxed">
                You have {todaysTasks.length} tasks scheduled for today with an estimated {todaysHoursEstimate} hours of work. 
                {completedTasks.length > 0 ? ` You've already completed ${completedTasks.length} tasks - great progress!` : ' Focus on your priorities and take breaks when needed.'}
              </p>
            </div>
          </div>

          {/* Upcoming Card */}
          <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2 px-1">
              <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
              UPCOMING 
              </span>
              <div className="w-4 h-4 flex items-center justify-center">
                <Clock size={16} className="text-gray-400" />
              </div>
            </div>
            <div className="space-y-2">
              <div className="space-y-1">
                <div className="flex gap-2">
                  <div className="px-2 py-1 bg-red-500/20 rounded-lg">
                    <span className="text-xs font-bold text-red-500">EXAM</span>
                  </div>
                  <div className="px-2 py-1 bg-red-500/20 rounded-lg">
                    <span className="text-xs font-bold text-red-500">HIGH</span>
                  </div>
                </div>
                <span className="text-sm text-white">Calculus Final Exam</span>
                <div className="text-xs text-gray-400">Today • 9:00 AM</div>
              </div>
            </div>
          </div>

          {/* Assignments Card */}
          <TasksCard />

          {/* To-Dos Card */}
          <SimpleTodosCard />
        </div>

        {/* Upcoming Calendar Events - Full Width Card */}
        <UpcomingCalendarCard />
      </div>

      {/* Overview Modal */}
      <div
        className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 transition-all duration-300 cursor-default ${
          showOverviewModal ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            setShowOverviewModal(false)
          }
        }}
      >
        <div 
          className={`bg-neutral-800 border border-gray-700/50 w-full max-w-2xl rounded-2xl max-h-[80vh] flex flex-col transition-all duration-300 ${
            showOverviewModal ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {showOverviewModal ? (
            <>
              {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700/50">
              <div>
                <h2 className="text-xl font-semibold text-white">Daily Overview</h2>
                <p className="text-sm text-gray-400 mt-1">
                  {new Date().toLocaleDateString('en-US', { 
                    weekday: 'long',
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </p>
              </div>
              <button 
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  setShowOverviewModal(false)
                }}
                className="p-2 hover:bg-neutral-800 rounded-lg transition-colors relative z-10"
                aria-label="Close modal"
                type="button"
              >
                <X size={24} className="text-gray-400 hover:text-white pointer-events-none" />
              </button>
            </div>

            {/* Content */}
            <div 
              className="flex-1 overflow-y-auto"
              style={{
                scrollbarWidth: 'auto',
                scrollbarColor: 'rgba(75, 85, 99, 0.5) transparent'
              }}
            >
              <div className="p-6">
                {/* Daily Briefing */}
                <div className="mb-8">
                  <div className="flex items-start gap-4 p-4 bg-neutral-700/50 rounded-lg">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                      <Zap size={20} className="text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-semibold text-white">Pulse</span>
                      </div>
                      <p className="text-sm text-gray-300 leading-relaxed">
                        {getGreeting()}! You have {todaysTasks.length} tasks scheduled for today, 
                        with an estimated {todaysHoursEstimate} hours of work. You've completed {completedTasks.length} tasks so far. 
                        {todaysTasks.length > 0 ? ' Focus on your priorities and take breaks when needed!' : ' Great job staying on top of things!'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Detailed Stats */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Today's Breakdown</h3>
                  
                  {/* Task Status Overview */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-neutral-700/50 rounded-lg p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <Calendar size={16} className="text-blue-400" />
                        <span className="text-sm font-medium text-white">Tasks Today</span>
                      </div>
                      <div className="text-2xl font-bold text-white">{todaysTasks.length}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {todaysHoursEstimate}h estimated
                      </div>
                    </div>
                    
                    <div className="bg-neutral-700/50 rounded-lg p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <CheckCircle size={16} className="text-green-400" />
                        <span className="text-sm font-medium text-white">Completed</span>
                      </div>
                      <div className="text-2xl font-bold text-white">{completedTasks.length}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {allTasks.length > 0 ? Math.round((completedTasks.length / allTasks.length) * 100) : 0}% of total
                      </div>
                    </div>
                  </div>

                  {/* Task Status Breakdown */}
                  <div className="space-y-3">
                    <h4 className="text-base font-semibold text-white">Task Status</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-neutral-700/30 rounded-lg">
                        <div className="flex items-center gap-3">
                          <AlertCircle size={14} className="text-yellow-400" />
                          <span className="text-sm text-white">Pending</span>
                        </div>
                        <span className="text-sm font-medium text-white">{pendingTasks.length}</span>
                      </div>
                      
                      <div className="flex items-center justify-between p-3 bg-neutral-700/30 rounded-lg">
                        <div className="flex items-center gap-3">
                          <PlayCircle size={14} className="text-blue-400" />
                          <span className="text-sm text-white">In Progress</span>
                        </div>
                        <span className="text-sm font-medium text-white">{inProgressTasks.length}</span>
                      </div>
                      
                      <div className="flex items-center justify-between p-3 bg-neutral-700/30 rounded-lg">
                        <div className="flex items-center gap-3">
                          <CheckCircle size={14} className="text-green-400" />
                          <span className="text-sm text-white">Completed</span>
                        </div>
                        <span className="text-sm font-medium text-white">{completedTasks.length}</span>
                      </div>
                    </div>
                  </div>

                  {/* Time Estimates */}
                  <div className="space-y-3">
                    <h4 className="text-base font-semibold text-white">Time Estimates</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-neutral-700/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Clock size={16} className="text-blue-400" />
                          <span className="text-sm font-medium text-white">Today</span>
                        </div>
                        <div className="text-xl font-bold text-white">{todaysHoursEstimate}h</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {todaysTasks.length} tasks
                        </div>
                      </div>
                      
                      <div className="bg-neutral-700/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Target size={16} className="text-purple-400" />
                          <span className="text-sm font-medium text-white">Total</span>
                        </div>
                        <div className="text-xl font-bold text-white">{hoursEstimate}h</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {allTasks.length} tasks
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}