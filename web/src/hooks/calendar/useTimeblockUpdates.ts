import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import { TIMEBLOCKS_CACHE_KEYS } from './useTimeblocks'
import { useWebSocket } from '@/contexts/WebSocketContext'

export const useTimeblockUpdates = () => {
  const queryClient = useQueryClient()
  const { socket } = useWebSocket()

  useEffect(() => {
    if (!socket) return

    // WebSocket listener for REAL-TIME timeblock updates (FASTEST - immediate UI sync)
    const handleTimeblockUpdate = (data: any) => {
      console.log('⚡️ REAL-TIME: Timeblock update via WebSocket', data)

      // Immediately invalidate cache to trigger refetch and update UI
      queryClient.invalidateQueries({ queryKey: TIMEBLOCKS_CACHE_KEYS.TIMEBLOCKS })
    }

    // Subscribe to WebSocket timeblock updates
    socket.on('timeblock_updated', handleTimeblockUpdate)

    // Set up Supabase real-time subscription for tasks (which are part of timeblocks)
    const tasksChannel = supabase
      .channel('tasks-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'tasks'
        },
        (payload) => {
          console.log('🔄 Task change detected, invalidating timeblocks cache')
          queryClient.invalidateQueries({ queryKey: TIMEBLOCKS_CACHE_KEYS.TIMEBLOCKS })
        }
      )
      .subscribe()

    // Set up Supabase real-time subscription for calendar events
    const eventsChannel = supabase
      .channel('calendar_events-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'calendar_events'
        },
        (payload) => {
          console.log('🔄 Calendar event change detected, invalidating timeblocks cache')
          queryClient.invalidateQueries({ queryKey: TIMEBLOCKS_CACHE_KEYS.TIMEBLOCKS })
        }
      )
      .subscribe()

    // Set up Supabase real-time subscription for busy blocks
    const busyChannel = supabase
      .channel('busy_blocks-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'busy_blocks'
        },
        (payload) => {
          console.log('🔄 Busy block change detected, invalidating timeblocks cache')
          queryClient.invalidateQueries({ queryKey: TIMEBLOCKS_CACHE_KEYS.TIMEBLOCKS })
        }
      )
      .subscribe()

    return () => {
      if (socket) {
        socket.off('timeblock_updated', handleTimeblockUpdate)
      }
      supabase.removeChannel(tasksChannel)
      supabase.removeChannel(eventsChannel)
      supabase.removeChannel(busyChannel)
    }
  }, [queryClient, socket])
}
