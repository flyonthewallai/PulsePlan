import { useMemo } from 'react'
import { Calendar, Loader2, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useTimeblocks } from '../hooks/useTimeblocks'
import { useTimeblockUpdates } from '../hooks/useTimeblockUpdates'
import { format, isToday, isTomorrow, isAfter } from 'date-fns'
import type { Timeblock } from '../types'

interface UpcomingCalendarCardProps {
  events?: Timeblock[]
}

export function UpcomingCalendarCard({ events }: UpcomingCalendarCardProps) {
  const navigate = useNavigate()
  
  // Enable real-time timeblock updates
  useTimeblockUpdates()
  
  // Use a shifting range that updates monthly but remains stable within each month
  const dateRange = useMemo(() => {
    const now = new Date()
    // Create a range that covers the current month + 3 months ahead
    // This shifts monthly but remains stable within each month
    const fromDate = new Date(now.getFullYear(), now.getMonth(), 1) // First day of current month
    const toDate = new Date(now.getFullYear(), now.getMonth() + 4, 0) // Last day of 3 months ahead
    
    return {
      fromISO: fromDate.toISOString(),
      toISO: toDate.toISOString()
    }
  }, [Math.floor(Date.now() / (1000 * 60 * 60 * 24 * 30))]) // Update every 30 days

  // Fetch real events using useTimeblocks with stable date range
  const { items: allEvents = [], isLoading, error } = useTimeblocks({
    fromISO: dateRange.fromISO,
    toISO: dateRange.toISO,
    enabled: !events // Only fetch if no events provided
  })

  // Use provided events or fetched events
  const eventsToProcess = events || allEvents

  // Memoize event processing to prevent unnecessary recalculations
  const processedEvents = useMemo(() => {
    const todayEvents: Timeblock[] = []
    const futureEvents: Timeblock[] = []
    
    eventsToProcess.forEach(event => {
      const eventDate = new Date(event.start)
      
      if (isToday(eventDate)) {
        todayEvents.push(event)
      } else if (isAfter(eventDate, new Date())) {
        futureEvents.push(event)
      }
    })
    
    // Sort today's events by start time
    todayEvents.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
    
    // Sort future events by start time
    futureEvents.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
    
    // Apply the logic: all today events + future events up to 4 total
    const totalTodayEvents = todayEvents.length
    const maxFutureEvents = Math.max(0, 4 - totalTodayEvents)
    const selectedFutureEvents = futureEvents.slice(0, maxFutureEvents)
    
    return {
      todayEvents,
      futureEvents: selectedFutureEvents
    }
  }, [eventsToProcess])

  const { todayEvents, futureEvents } = processedEvents

  // Format time for display
  const formatEventTime = (event: Timeblock) => {
    if (event.isAllDay) {
      return 'All day'
    }
    
    const start = new Date(event.start)
    const end = new Date(event.end)
    
    const startTime = format(start, 'h:mm a')
    const endTime = format(end, 'h:mm a')
    
    return `${startTime} - ${endTime}`
  }

  // Format date for display
  const formatEventDate = (event: Timeblock) => {
    // Parse the date string and extract just the date part to avoid timezone issues
    const dateStr = event.start.split('T')[0] // Get just the date part (YYYY-MM-DD)
    const eventDate = new Date(dateStr + 'T00:00:00') // Force local timezone interpretation
    
    if (isToday(eventDate)) {
      return 'Today'
    } else if (isTomorrow(eventDate)) {
      return 'Tomorrow'
    } else {
      return format(eventDate, 'MMM d')
    }
  }

  if (isLoading) {
    return (
      <div className="w-full">
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4 px-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
              CALENDAR
            </span>
            <div className="w-4 h-4 flex items-center justify-center">
              <Calendar size={16} className="text-gray-400" />
            </div>
          </div>
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="w-8 h-8 bg-gray-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <Loader2 size={16} className="text-gray-400 animate-spin" />
              </div>
              <div className="text-sm font-medium text-gray-400 mb-1">
                Loading events...
              </div>
              <div className="text-xs text-gray-400">
                Please wait
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full">
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4 px-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
              CALENDAR
            </span>
            <div className="w-4 h-4 flex items-center justify-center">
              <Calendar size={16} className="text-gray-400" />
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-4 h-4 rounded-full border-2 border-red-500 flex items-center justify-center mt-0.5">
                <X size={10} className="text-red-400" />
              </div>
              <div className="flex-1">
                <span className="text-sm font-medium text-red-400">
                  Error loading events
                </span>
                <div className="text-xs text-gray-500 mt-1">
                  {error instanceof Error ? error.message : 'Failed to load events'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4 px-1">
          <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
            CALENDAR
          </span>
          <div className="w-4 h-4 flex items-center justify-center">
            <Calendar size={16} className="text-gray-400" />
          </div>
        </div>
        
        <div className="space-y-4">
          {/* Today Section */}
          {todayEvents.length > 0 && (
          <div>
            <div className="text-sm font-medium text-white mb-3">Today</div>
            <div className="space-y-2">
                {todayEvents.map((event) => (
                 <div key={event.id} className="relative">
                   <div className="flex items-center py-2">
                     {/* Vertical blue line for timed events */}
                     {!event.isAllDay && (
                       <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-full"></div>
                     )}
                     
                     {/* Blue dot for all-day events */}
                     {event.isAllDay && (
                       <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full"></div>
                     )}
                     
                     <div className="flex-1 ml-6">
                       <div className="text-sm text-white font-medium">{event.title}</div>
                        <div className="text-xs text-gray-400">{formatEventTime(event)}</div>
                     </div>
                   </div>
                 </div>
               ))}
            </div>
          </div>
          )}

          {/* Future Events Section */}
          {futureEvents.length > 0 && (
            <div>
              <div className="text-sm font-medium text-white mb-3">Upcoming</div>
            <div className="space-y-2">
                {futureEvents.map((event) => (
                 <div key={event.id} className="relative">
                   <div className="flex items-center py-2">
                     {/* Vertical blue line for timed events */}
                     {!event.isAllDay && (
                       <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-full"></div>
                     )}
                     
                     {/* Blue dot for all-day events */}
                     {event.isAllDay && (
                       <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full"></div>
                     )}
                     
                     <div className="flex-1 ml-6">
                       <div className="text-sm text-white font-medium">{event.title}</div>
                        <div className="text-xs text-gray-400">
                          {formatEventDate(event)} • {formatEventTime(event)}
                        </div>
                     </div>
                   </div>
                 </div>
               ))}
            </div>
          </div>
          )}

          {/* No events message */}
          {todayEvents.length === 0 && futureEvents.length === 0 && (
            <div className="text-sm text-gray-400 text-center py-4">
              No upcoming events
            </div>
          )}
        </div>
        
        {/* View all link */}
        <div className="mt-4 pt-3">
          <button 
            onClick={() => navigate('/calendar')}
            className="text-xs text-gray-400 hover:text-white transition-colors"
          >
            View all events →
          </button>
        </div>
      </div>
    </div>
  )
}
