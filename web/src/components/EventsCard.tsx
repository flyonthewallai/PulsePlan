import React, { useState } from 'react'
import { X, Calendar, Clock, MapPin, Users, Video } from 'lucide-react'

interface Event {
  id: string
  title: string
  type: 'exam' | 'meeting' | 'class' | 'deadline' | 'social' | 'appointment'
  subject?: string
  start_date: string
  end_date?: string
  location?: string
  location_type?: 'virtual'
  meeting_url?: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  status: 'scheduled'
  preparation_time_minutes?: number
  attendees?: string[]
}

export function EventsCard() {
  const [events, setEvents] = useState<Event[]>([
    {
      id: '1',
      title: 'Calculus Final Exam',
      type: 'exam',
      subject: 'Mathematics',
      start_date: '2024-03-25T09:00:00Z',
      end_date: '2024-03-25T11:00:00Z',
      location: 'Room 101, Science Building',
      priority: 'high',
      status: 'scheduled',
      preparation_time_minutes: 120,
    },
    {
      id: '2',
      title: 'Team Project Meeting',
      type: 'meeting',
      start_date: '2024-03-24T14:00:00Z',
      end_date: '2024-03-24T15:00:00Z',
      location_type: 'virtual',
      meeting_url: 'https://zoom.us/j/123456789',
      priority: 'medium',
      status: 'scheduled',
      attendees: ['teammate1@email.com', 'teammate2@email.com'],
    },
    {
      id: '3',
      title: 'Computer Science Lecture',
      type: 'class',
      subject: 'Computer Science',
      start_date: '2024-03-24T10:00:00Z',
      end_date: '2024-03-24T11:30:00Z',
      location: 'Lecture Hall A',
      priority: 'medium',
      status: 'scheduled',
    },
    {
      id: '4',
      title: 'Study Group Session',
      type: 'social',
      subject: 'Physics',
      start_date: '2024-03-23T16:00:00Z',
      end_date: '2024-03-23T18:00:00Z',
      location: 'Library Study Room 3',
      priority: 'low',
      status: 'scheduled',
    },
    {
      id: '5',
      title: 'Assignment Due',
      type: 'deadline',
      subject: 'English',
      start_date: '2024-03-26T23:59:00Z',
      priority: 'high',
      status: 'scheduled',
    },
  ])
  const [showModal, setShowModal] = useState(false)
  const [currentEventIndex, setCurrentEventIndex] = useState(0)

  // Filter to upcoming events
  const upcomingEvents = events.filter(event => 
    new Date(event.start_date) >= new Date() && event.status === 'scheduled'
  )

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'exam': return '#FF3B30'
      case 'meeting': return '#007AFF'
      case 'class': return '#34C759'
      case 'deadline': return '#FF9500'
      case 'social': return '#AF52DE'
      case 'appointment': return '#5AC8FA'
      default: return '#8E8E93'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#FF3B30'
      case 'medium': return '#FF9500'
      case 'low': return '#34C759'
      case 'critical': return '#FF0000'
      default: return '#8E8E93'
    }
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

  const getEventIcon = (event: Event) => {
    if (event.location_type === 'virtual' || event.meeting_url) {
      return <Video size={12} className="text-gray-400" />
    }
    if (event.attendees && event.attendees.length > 0) {
      return <Users size={12} className="text-gray-400" />
    }
    if (event.location) {
      return <MapPin size={12} className="text-gray-400" />
    }
    return <Calendar size={12} className="text-gray-400" />
  }

  const getEventTypeLabel = (type: string) => {
    switch (type) {
      case 'exam': return 'EXAM'
      case 'meeting': return 'MEETING'
      case 'class': return 'CLASS'
      case 'deadline': return 'DEADLINE'
      case 'social': return 'SOCIAL'
      case 'appointment': return 'APPOINTMENT'
      default: return type.toUpperCase()
    }
  }

  const currentEvent = upcomingEvents[currentEventIndex] || upcomingEvents[0]

  return (
    <>
      {/* Section Header */}
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
          EVENTS
        </span>
        <div className="w-4 h-4 flex items-center justify-center">
          <div className="w-3 h-3 border border-gray-400 rounded-sm"></div>
        </div>
      </div>

      {/* Card */}
      <div 
        className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4 mb-6 cursor-pointer hover:bg-neutral-800 transition-colors"
        onClick={() => setShowModal(true)}
      >
        <div className="space-y-2">
          {/* Current event item */}
          <div className="space-y-3">
            <div className="flex gap-2">
              <div 
                className="px-2 py-1 rounded-lg"
                style={{ backgroundColor: getTypeColor(currentEvent?.type || 'other') + '20' }}
              >
                <span 
                  className="text-xs font-bold tracking-wider"
                  style={{ color: getTypeColor(currentEvent?.type || 'other') }}
                >
                  {getEventTypeLabel(currentEvent?.type || 'other')}
                </span>
              </div>
              <div 
                className="px-2 py-1 rounded-lg"
                style={{ backgroundColor: getPriorityColor(currentEvent?.priority || 'medium') + '20' }}
              >
                <span 
                  className="text-xs font-bold tracking-wider"
                  style={{ color: getPriorityColor(currentEvent?.priority || 'medium') }}
                >
                  {currentEvent?.priority?.toUpperCase() || 'MEDIUM'}
                </span>
              </div>
            </div>
            
            <div className="space-y-1">
              <span className="text-base font-semibold text-white">
                {currentEvent?.title || 'No upcoming events'}
              </span>
              
              {currentEvent && (
                <>
                  {currentEvent.subject && (
                    <div className="text-sm font-medium text-gray-400 opacity-80">
                      {currentEvent.subject}
                    </div>
                  )}
                  
                  <div className="flex items-center gap-3 flex-wrap mt-1">
                    <div className="flex items-center gap-1">
                      <Calendar size={12} className="text-gray-400" />
                      <span className="text-xs font-medium text-gray-400">
                        {formatDate(currentEvent.start_date)}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock size={12} className="text-gray-400" />
                      <span className="text-xs font-medium text-gray-400">
                        {formatTime(currentEvent.start_date)}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      {getEventIcon(currentEvent)}
                      <span className="text-xs font-medium text-gray-400">
                        {currentEvent.location || 
                         (currentEvent.location_type === 'virtual' ? 'Virtual' : 
                          currentEvent.attendees ? `${currentEvent.attendees.length} attendees` : 'Event')}
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Status indicator */}
          {upcomingEvents.length > 1 && (
            <div className="text-sm text-gray-400 text-center mt-1">
              {currentEventIndex + 1} of {upcomingEvents.length}
            </div>
          )}

          {/* Progress indicators */}
          <div className="flex items-center justify-center gap-2 mt-1">
            {upcomingEvents.slice(0, 4).map((event, index) => (
              <div
                key={event.id}
                className={`w-2 h-2 rounded-full`}
                style={{ backgroundColor: getTypeColor(event.type) }}
                {...(index === currentEventIndex && { className: 'w-2 h-2 rounded-full border border-white/60' })}
              />
            ))}
            {upcomingEvents.length > 4 && (
              <span className="text-gray-500 text-base font-semibold">•••</span>
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50">
          <div className="bg-gray-900 w-full max-w-md rounded-t-2xl max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-5 pt-8">
              <button onClick={() => setShowModal(false)}>
                <X size={24} className="text-white" />
              </button>
              <h2 className="text-lg font-semibold text-white">Events</h2>
              <div className="w-6"></div>
            </div>

            {/* Events list */}
            <div className="flex-1 px-4 overflow-y-auto">
              {upcomingEvents.map((event) => (
                <div
                  key={event.id}
                  className="p-4 bg-neutral-800 rounded-xl mb-2"
                >
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <div 
                        className="px-2 py-1 rounded-lg"
                        style={{ backgroundColor: getTypeColor(event.type) + '20' }}
                      >
                        <span 
                          className="text-xs font-bold tracking-wider"
                          style={{ color: getTypeColor(event.type) }}
                        >
                          {getEventTypeLabel(event.type)}
                        </span>
                      </div>
                      <div 
                        className="px-2 py-1 rounded-lg"
                        style={{ backgroundColor: getPriorityColor(event.priority) + '20' }}
                      >
                        <span 
                          className="text-xs font-bold tracking-wider"
                          style={{ color: getPriorityColor(event.priority) }}
                        >
                          {event.priority.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    
                    <div className="text-base font-semibold text-white">
                      {event.title}
                    </div>
                    
                    {event.subject && (
                      <div className="text-sm font-medium text-gray-400 opacity-80">
                        {event.subject}
                      </div>
                    )}
                    
                    <div className="flex items-center gap-3 flex-wrap mt-1">
                      <div className="flex items-center gap-1">
                        <Calendar size={12} className="text-gray-400" />
                        <span className="text-xs font-medium text-gray-400">
                          {formatDate(event.start_date)}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock size={12} className="text-gray-400" />
                        <span className="text-xs font-medium text-gray-400">
                          {formatTime(event.start_date)}
                          {event.end_date && ` - ${formatTime(event.end_date)}`}
                        </span>
                      </div>
                      {(event.location || event.location_type === 'virtual' || event.attendees) && (
                        <div className="flex items-center gap-1">
                          {getEventIcon(event)}
                          <span className="text-xs font-medium text-gray-400">
                            {event.location || 
                             (event.location_type === 'virtual' ? 'Virtual Meeting' : 
                              event.attendees ? `${event.attendees.length} attendees` : 'Event')}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {upcomingEvents.length === 0 && (
                <div className="text-center py-10">
                  <div className="text-base font-semibold text-gray-400 mb-1">
                    No upcoming events
                  </div>
                  <div className="text-sm text-gray-400">
                    Create a new event to get started
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
