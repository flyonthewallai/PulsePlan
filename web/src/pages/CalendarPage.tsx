import { useState, useCallback, useRef, useEffect } from 'react'
import { usePageTitle } from '../hooks/usePageTitle'
import { useNavigate } from 'react-router-dom'
import { format, addDays, addMonths } from 'date-fns'
import { WeeklyCalendar } from '../features/calendar/WeeklyCalendar'
import { DailyCalendar } from '../features/calendar/DailyCalendar'
import { MonthlyCalendar } from '../features/calendar/MonthlyCalendar'
import { CalendarDayHeader } from '../features/calendar/components/CalendarDayHeader'
import { CalendarRightSidebar } from '../features/calendar/components/CalendarRightSidebar'
import { PulseChatSidebar } from '../features/calendar/components/PulseChatSidebar'
import { TaskModal } from '../features/tasks/TaskModal'
import PulseTrace from '../components/PulseTrace'
import { ChevronLeft, ChevronRight, ChevronDown, PenSquare, Check } from 'lucide-react'
import { agentAPI } from '../lib/api/sdk'
import { useProfile } from '../hooks/useProfile'
import type { Task, CalendarEvent } from '../types'

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}

type CalendarView = 'day' | 'week' | 'month'

export function CalendarPage() {
  usePageTitle('Calendar')
  const navigate = useNavigate()
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [showTaskModal, setShowTaskModal] = useState(false)
  const [newEventData, setNewEventData] = useState<{ start: string; end: string } | null>(null)
  const [showPulseChat, setShowPulseChat] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)
  const [conversationName, setConversationName] = useState<string>('New conversation')
  const messagesEndRef = useRef<HTMLDivElement>(null!)
  const tooltipTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const inactivityTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // Profile for greeting personalization
  const { data: profile } = useProfile()
  const displayName = profile?.full_name?.split(' ')[0] || 'there'
  
  // Calendar state
  const [currentDate, setCurrentDate] = useState(new Date())
  const [calendarView, setCalendarView] = useState<CalendarView>('week')
  const [showViewDropdown, setShowViewDropdown] = useState(false)
  
  // Mock calendar accounts - replace with real data from API
  const [calendars, setCalendars] = useState([
    {
      id: '1',
      name: 'connergroth@gmail.com',
      email: 'connergroth@gmail.com',
      color: '#4285F4',
      icon: 'google' as const,
      isVisible: true,
      isDefault: true,
    },
    {
      id: '2',
      name: 'Holidays in United States',
      email: '',
      color: '#0B8043',
      icon: 'google' as const,
      isVisible: true,
    },
  ])

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

  const handlePulseOpen = () => {
    setShowPulseChat(true)
    resetInactivityTimer()
  }

  const handlePulseClose = () => {
    setShowPulseChat(false)
    setInputValue('')
    if (inactivityTimeoutRef.current) {
      clearTimeout(inactivityTimeoutRef.current)
    }
  }

  const resetInactivityTimer = () => {
    if (inactivityTimeoutRef.current) {
      clearTimeout(inactivityTimeoutRef.current)
    }
    // Auto-close after 5 minutes of inactivity
    inactivityTimeoutRef.current = setTimeout(() => {
      if (!isTyping && messages.length > 0) {
        handlePulseClose()
      }
    }, 300000) // 5 minutes
  }

  // Calendar navigation handlers
  const handlePrevious = useCallback(() => {
    if (calendarView === 'day') {
      setCurrentDate(prev => addDays(prev, -1))
    } else if (calendarView === 'week') {
      setCurrentDate(prev => new Date(prev.getTime() - 7 * 24 * 60 * 60 * 1000))
    } else {
      setCurrentDate(prev => addMonths(prev, -1))
    }
  }, [calendarView])

  const handleNext = useCallback(() => {
    if (calendarView === 'day') {
      setCurrentDate(prev => addDays(prev, 1))
    } else if (calendarView === 'week') {
      setCurrentDate(prev => new Date(prev.getTime() + 7 * 24 * 60 * 60 * 1000))
    } else {
      setCurrentDate(prev => addMonths(prev, 1))
    }
  }, [calendarView])

  const handleToday = useCallback(() => {
    setCurrentDate(new Date())
  }, [])

  const handleNewEventClick = useCallback(() => {
    const now = new Date()
    const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000)
    
    setNewEventData({
      start: now.toISOString(),
      end: oneHourLater.toISOString(),
    })
    setSelectedTask(null)
    setShowTaskModal(true)
  }, [])

  // Calendar sidebar handlers
  const handleDateSelect = useCallback((date: Date) => {
    setCurrentDate(date)
  }, [])

  const handleCalendarToggle = useCallback((calendarId: string) => {
    setCalendars(prev =>
      prev.map(cal =>
        cal.id === calendarId ? { ...cal, isVisible: !cal.isVisible } : cal
      )
    )
  }, [])

  // Generate conversation name based on first message
  const generateConversationName = (firstMessage: string) => {
    const words = firstMessage.trim().split(' ')
    if (words.length <= 3) {
      return firstMessage.trim()
    }
    return words.slice(0, 3).join(' ') + '...'
  }

  const handleFullscreenClick = () => {
    // Navigate to chat with current conversation context
    const conversationData = {
      messages: messages,
      inputValue: inputValue
    }
    navigate('/chat', { 
      state: { 
        conversationContext: conversationData,
        fromCalendar: true 
      } 
    })
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isTyping) return

    resetInactivityTimer() // Reset timer on user activity

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue.trim(),
      isUser: true,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    
    // Update conversation name if this is the first message
    if (messages.length === 0) {
      setConversationName(generateConversationName(userMessage.text))
    }
    
    setInputValue('')
    setIsTyping(true)

    try {
      const context = {
        currentPage: 'calendar',
        timestamp: new Date().toISOString()
      }

      const response = await agentAPI.sendQuery({
        query: userMessage.text,
        context
      })

      let responseText = ''
      if (response?.success !== false && response) {
        if ((response as any).immediate_response) {
          responseText = (response as any).immediate_response
        } else if (response.data && response.data.response) {
          responseText = response.data.response
        } else if (response.data && response.data.message) {
          responseText = response.data.message
        } else if ((response as any).response) {
          responseText = (response as any).response
        } else if (response.message) {
          responseText = response.message
        } else if (typeof response === 'string') {
          responseText = response
        } else if (response.data) {
          if (typeof response.data === 'string') {
            responseText = response.data
          } else if (response.data.summary) {
            responseText = response.data.summary
          }
        }
      }

      if (responseText) {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: responseText,
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, aiMessage])
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle 'p' key to open/close pulse chat
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'p' || e.key === 'P') {
        // Don't trigger if user is typing in an input/textarea
        const target = e.target as HTMLElement
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
          return
        }
        e.preventDefault()
        
        if (showPulseChat) {
          handlePulseClose()
        } else {
          handlePulseOpen()
        }
      }
    }

    document.addEventListener('keydown', handleKeyPress)
    return () => {
      document.removeEventListener('keydown', handleKeyPress)
    }
  }, [showPulseChat])

  // Handle D/W/M keys to switch calendar views
  useEffect(() => {
    const handleViewShortcut = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input/textarea
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return
      }

      const key = e.key.toLowerCase()
      if (key === 'd') {
        e.preventDefault()
        setCalendarView('day')
      } else if (key === 'w') {
        e.preventDefault()
        setCalendarView('week')
      } else if (key === 'm') {
        e.preventDefault()
        setCalendarView('month')
      }
    }

    document.addEventListener('keydown', handleViewShortcut)
    return () => {
      document.removeEventListener('keydown', handleViewShortcut)
    }
  }, [])

  // Handle tooltip hover with delay
  const handleMouseEnter = () => {
    tooltipTimeoutRef.current = setTimeout(() => {
      setShowTooltip(true)
    }, 1500) // 1.5 second delay
  }

  const handleMouseLeave = () => {
    if (tooltipTimeoutRef.current) {
      clearTimeout(tooltipTimeoutRef.current)
      tooltipTimeoutRef.current = null
    }
    setShowTooltip(false)
  }

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (tooltipTimeoutRef.current) {
        clearTimeout(tooltipTimeoutRef.current)
      }
    }
  }, [])

  // Close dropdown on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showViewDropdown) {
        setShowViewDropdown(false)
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [showViewDropdown])

  return (
    <div className="flex h-screen w-full overflow-hidden" style={{ backgroundColor: '#0B0B0B' }}>
      {/* Main Calendar Container */}
      <div className="flex flex-1 overflow-hidden">
        {/* Calendar Area with Header */}
        <div className="flex flex-col flex-1">
          {/* Fixed Top Header - Notion Style */}
          <header className="flex items-center justify-between px-8 py-3 border-b border-white/5" style={{ backgroundColor: '#111111' }}>
            {/* Left: Month/Year */}
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-[#E5E5E5]">
                {format(currentDate, 'MMMM yyyy')}
              </h1>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-2">
            {/* View Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowViewDropdown(!showViewDropdown)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-800/40 border border-gray-700/50 rounded-lg hover:bg-neutral-800/60 transition-colors text-[#E5E5E5] text-sm font-medium"
              >
                {calendarView.charAt(0).toUpperCase() + calendarView.slice(1)}
                <ChevronDown size={14} className="text-gray-400" />
              </button>

              {showViewDropdown && (
                <div 
                  className="absolute top-full right-0 mt-1 bg-[#1a1a1a] border border-white/10 rounded-lg shadow-lg py-1 min-w-[180px] z-50"
                  onMouseLeave={() => setShowViewDropdown(false)}
                >
                  <button
                    onClick={() => {
                      setCalendarView('day')
                      setShowViewDropdown(false)
                    }}
                    className="w-full px-3 py-1.5 text-left text-sm text-[#E5E5E5] hover:bg-white/5 transition-colors flex items-center justify-between gap-4"
                  >
                    <div className="flex items-center gap-2">
                      {calendarView === 'day' && <Check size={14} className="text-white" />}
                      {calendarView !== 'day' && <span className="w-3.5" />}
                      <span>Day</span>
                    </div>
                    <span className="text-xs text-gray-500">D</span>
                  </button>
                  <button
                    onClick={() => {
                      setCalendarView('week')
                      setShowViewDropdown(false)
                    }}
                    className="w-full px-3 py-1.5 text-left text-sm text-[#E5E5E5] hover:bg-white/5 transition-colors flex items-center justify-between gap-4"
                  >
                    <div className="flex items-center gap-2">
                      {calendarView === 'week' && <Check size={14} className="text-white" />}
                      {calendarView !== 'week' && <span className="w-3.5" />}
                      <span>Week</span>
                    </div>
                    <span className="text-xs text-gray-500">W</span>
                  </button>
                  <button
                    onClick={() => {
                      setCalendarView('month')
                      setShowViewDropdown(false)
                    }}
                    className="w-full px-3 py-1.5 text-left text-sm text-[#E5E5E5] hover:bg-white/5 transition-colors flex items-center justify-between gap-4"
                  >
                    <div className="flex items-center gap-2">
                      {calendarView === 'month' && <Check size={14} className="text-white" />}
                      {calendarView !== 'month' && <span className="w-3.5" />}
                      <span>Month</span>
                    </div>
                    <span className="text-xs text-gray-500">M</span>
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={handleToday}
              className="px-3 py-1.5 bg-neutral-800/40 border border-gray-700/50 rounded-lg hover:bg-neutral-800/60 transition-colors text-[#E5E5E5] text-sm font-medium"
            >
              Today
            </button>

            {/* Navigation arrows */}
            <div className="flex items-center gap-0.5">
              <button
                onClick={handlePrevious}
                className="p-1.5 hover:bg-white/5 rounded-md transition-colors text-gray-400 hover:text-white"
                aria-label="Previous"
              >
                <ChevronLeft size={16} />
              </button>

              <button
                onClick={handleNext}
                className="p-1.5 hover:bg-white/5 rounded-md transition-colors text-gray-400 hover:text-white"
                aria-label="Next"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            <div className="w-px h-5 bg-white/10 mx-1" />

            {/* Icon buttons */}
            <button
              onClick={handlePulseOpen}
              className="p-2 hover:bg-white/5 rounded-md transition-colors text-gray-400 hover:text-white"
              title="AI Schedule"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
              </svg>
            </button>

            <button
              onClick={handleNewEventClick}
              className="p-2 hover:bg-white/5 rounded-md transition-colors text-gray-400 hover:text-white"
              title="New Event"
            >
              <PenSquare size={16} />
            </button>
          </div>
        </header>

        {/* Calendar Grid Container */}
        <div className="flex-1 flex flex-col overflow-hidden relative" style={{ backgroundColor: '#111111' }}>
          {/* Sticky Day Header - Notion Style (only for day/week views) */}
          {calendarView !== 'month' && (
            <div className="sticky top-0 z-30 px-8" style={{ backgroundColor: '#111111' }}>
              <CalendarDayHeader 
                currentDate={currentDate} 
                viewMode={calendarView as 'day' | 'week'} 
              />
            </div>
          )}

          {/* Scrollable Calendar */}
          <div className="flex-1 overflow-y-auto px-8 pb-8" style={{ backgroundColor: '#111111' }}>
            <div className="h-full min-h-full">
              {calendarView === 'day' && (
                <DailyCalendar
                  currentDate={currentDate}
                  onEventClick={handleEventClick}
                  className="h-full w-full"
                />
              )}
              {calendarView === 'week' && (
                <WeeklyCalendar
                  currentDate={currentDate}
                  onEventClick={handleEventClick}
                  className="h-full w-full"
                />
              )}
              {calendarView === 'month' && (
                <MonthlyCalendar
                  currentDate={currentDate}
                  onEventClick={handleEventClick}
                  onCreateEvent={handleCreateEvent}
                  onDayClick={(date) => {
                    setCurrentDate(date)
                    setCalendarView('day')
                  }}
                  className="h-full w-full"
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Conditional (Calendar or Chat) */}
      {showPulseChat ? (
        <PulseChatSidebar
          messages={messages}
          inputValue={inputValue}
          isTyping={isTyping}
          conversationName={conversationName}
          onClose={handlePulseClose}
          onInputChange={setInputValue}
          onSendMessage={handleSendMessage}
          onFullscreen={handleFullscreenClick}
          messagesEndRef={messagesEndRef}
          userName={displayName}
        />
      ) : (
        <CalendarRightSidebar
          currentDate={currentDate}
          onDateSelect={handleDateSelect}
          calendars={calendars}
          onCalendarToggle={handleCalendarToggle}
        />
      )}
      </div>

      {/* Task Modal */}
      {showTaskModal && (
        <TaskModal
          task={selectedTask}
          initialData={newEventData}
          onClose={handleCloseModal}
        />
      )}

      {/* Pulse Orb - toggles sidebar */}
      {!showPulseChat && (
      <div className="fixed bottom-6 right-6 z-50">
        <button
            onClick={handlePulseOpen}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          className="w-16 h-16 bg-neutral-800/80 border border-gray-700/50 rounded-full flex items-center justify-center shadow-lg backdrop-blur-sm hover:bg-neutral-700/80 transition-colors"
        >
          <PulseTrace active={true} width={32} height={32} />
        </button>
        
        {/* Tooltip */}
        <div className={`absolute bottom-full right-0 mb-2 transition-opacity duration-200 pointer-events-none ${
          showTooltip ? 'opacity-100' : 'opacity-0'
        }`}>
          <div className="bg-neutral-800/90 border border-gray-600/50 rounded-lg px-3 py-2 shadow-lg backdrop-blur-sm">
            <p className="text-white text-sm whitespace-nowrap">Press 'P' anywhere to summon Pulse</p>
          </div>
          {/* Arrow pointing down */}
          <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-neutral-800/90"></div>
          </div>
        </div>
      )}
    </div>
  )
}