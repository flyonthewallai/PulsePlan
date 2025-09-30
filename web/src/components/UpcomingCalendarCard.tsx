import React from 'react'
import { Calendar } from 'lucide-react'

interface CalendarEvent {
  id: string
  title: string
  time: string
  date: string
  isAllDay?: boolean
}

interface UpcomingCalendarCardProps {
  events?: CalendarEvent[]
}

export function UpcomingCalendarCard({ events = [] }: UpcomingCalendarCardProps) {
  // Mock data matching the exact image
  const mockEvents = {
    today: [
      {
        id: '1',
        title: 'Sleepers going to SPIN',
        time: '8 - 9PM',
        date: 'Today',
        isAllDay: false
      }
    ],
    tomorrow: [
      {
        id: '2',
        title: 'User Interviews',
        time: 'All day',
        date: 'Tomorrow',
        isAllDay: true
      },
      {
        id: '3',
        title: 'Dawson Chen and Charles Piper',
        time: '2:00 - 3:30PM',
        date: 'Tomorrow',
        isAllDay: false
      }
    ]
  }

  const displayEvents = events.length > 0 ? events : [...mockEvents.today, ...mockEvents.tomorrow]

  return (
    <div className="w-full">
      <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
        <div className="flex items-center justify-between mb-4 px-1">
          <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
            CALENDAR
          </span>
          <div className="w-4 h-4 flex items-center justify-center">
            <Calendar size={14} className="text-gray-400" />
          </div>
        </div>
        
        <div className="space-y-4">
          {/* Today Section */}
          <div>
            <div className="text-sm font-medium text-white mb-3">Today</div>
            <div className="space-y-2">
               {mockEvents.today.map((event) => (
                 <div key={event.id} className="relative">
                   <div className="flex items-center gap-3 py-2">
                     {/* Vertical yellow line for timed events */}
                     {!event.isAllDay && (
                       <div className="absolute left-0 top-0 bottom-0 w-1 bg-yellow-500 rounded-full"></div>
                     )}
                     
                     {/* Yellow dot for all-day events */}
                     {event.isAllDay && (
                       <div className="w-2 h-2 bg-yellow-500 rounded-full flex-shrink-0 ml-1"></div>
                     )}
                     
                     <div className="flex-1 ml-6">
                       <div className="text-sm text-white font-medium">{event.title}</div>
                       <div className="text-xs text-gray-400">{event.time}</div>
                     </div>
                   </div>
                 </div>
               ))}
            </div>
          </div>

          {/* Tomorrow Section */}
          <div>
            <div className="text-sm font-medium text-white mb-3">Tomorrow</div>
            <div className="space-y-2">
               {mockEvents.tomorrow.map((event) => (
                 <div key={event.id} className="relative">
                   <div className="flex items-center gap-3 py-2">
                     {/* Vertical yellow line for timed events */}
                     {!event.isAllDay && (
                       <div className="absolute left-0 top-0 bottom-0 w-1 bg-yellow-500 rounded-full"></div>
                     )}
                     
                     {/* Yellow dot for all-day events */}
                     {event.isAllDay && (
                       <div className="w-2 h-2 bg-yellow-500 rounded-full flex-shrink-0 ml-1"></div>
                     )}
                     
                     <div className="flex-1 ml-6">
                       <div className="text-sm text-white font-medium">{event.title}</div>
                       <div className="text-xs text-gray-400">{event.time}</div>
                     </div>
                   </div>
                 </div>
               ))}
            </div>
          </div>
        </div>
        
        {/* View all link */}
        <div className="mt-4 pt-3">
          <button className="text-xs text-gray-400 hover:text-white transition-colors">
            View all events →
          </button>
        </div>
      </div>
    </div>
  )
}
