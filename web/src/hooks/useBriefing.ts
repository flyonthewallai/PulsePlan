import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { BRIEFING_CACHE_KEYS } from './cacheKeys'
import { apiClient } from '../lib/api/client'

interface BriefingContent {
  summary: string
  greeting?: string
  tasks?: any[]
  events?: any[]
  priorities?: any[]
  recommendations?: any[]
  free_time_blocks?: string
  reschedule_summary?: string
  tasks_count?: number
  deadlines_count?: number
  today_tasks?: any[]
  upcoming_deadlines?: any[]
  raw_result?: any
}

interface Briefing {
  id: string
  user_id: string
  briefing_date: string
  content: BriefingContent
  generated_at: string
  created_at: string
}

interface TestBriefingRequest {
  send_email?: boolean
  send_notification?: boolean
}

interface TestBriefingResponse {
  success: boolean
  briefing?: BriefingContent
  email_sent: boolean
  notification_sent: boolean
  message: string
}

// API functions
const fetchTodaysBriefing = async (): Promise<Briefing> => {
  const response = await apiClient.get<Briefing>('/api/v1/briefings/today')

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

const sendTestBriefing = async (request: TestBriefingRequest): Promise<TestBriefingResponse> => {
  const response = await apiClient.post<TestBriefingResponse>(
    '/api/v1/briefings/send-test',
    request
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

/**
 * Hook to fetch today's briefing
 * Caches for 24 hours and auto-invalidates at midnight
 */
export const useTodaysBriefing = () => {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: BRIEFING_CACHE_KEYS.TODAY,
    queryFn: fetchTodaysBriefing,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours - briefing valid all day
    gcTime: 48 * 60 * 60 * 1000, // 48 hours garbage collection (was cacheTime in v4)
    refetchOnWindowFocus: false, // Don't regenerate on tab switch
    refetchOnMount: false, // Use cached version
    retry: 2,
  })

  // Auto-invalidate at midnight
  useEffect(() => {
    const now = new Date()
    const tomorrow = new Date(now)
    tomorrow.setDate(tomorrow.getDate() + 1)
    tomorrow.setHours(0, 0, 0, 0)

    const timeUntilMidnight = tomorrow.getTime() - now.getTime()

    const timer = setTimeout(() => {
      // Invalidate briefing cache at midnight
      queryClient.invalidateQueries({ queryKey: BRIEFING_CACHE_KEYS.TODAY })

      // Set up recurring invalidation every 24 hours
      const dailyInvalidation = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: BRIEFING_CACHE_KEYS.TODAY })
      }, 24 * 60 * 60 * 1000)

      return () => clearInterval(dailyInvalidation)
    }, timeUntilMidnight)

    return () => clearTimeout(timer)
  }, [queryClient])

  return query
}

/**
 * Hook to send test briefing
 * Invalidates briefing cache on success
 */
export const useSendTestBriefing = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: sendTestBriefing,
    onSuccess: () => {
      // Invalidate today's briefing to fetch the freshly generated one
      queryClient.invalidateQueries({ queryKey: BRIEFING_CACHE_KEYS.TODAY })
    },
    onError: (error) => {
      console.error('Failed to send test briefing:', error)
    }
  })
}

/**
 * Utility function to invalidate all briefing-related queries
 */
export const invalidateBriefingQueries = (queryClient: any) => {
  queryClient.invalidateQueries({ queryKey: ['briefing'] })
}
