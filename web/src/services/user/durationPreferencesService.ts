import { apiClient } from '@/lib/api/client'

export interface DurationPreference {
  id: string
  user_id: string
  category: string
  estimated_minutes: number
  confidence: number
  created_at: string
  updated_at: string
}

export interface CourseDurationPreference {
  id: string
  user_id: string
  course_id: string
  category: string
  estimated_minutes: number
  created_at: string
  updated_at: string
}

export interface DurationPreferenceCreate {
  category: string
  estimated_minutes: number
  confidence?: number
}

export interface CourseDurationPreferenceCreate {
  course_id: string
  category: string
  estimated_minutes: number
}

export const durationPreferencesApi = {
  // Global preferences
  getGlobal: async (): Promise<DurationPreference[]> => {
    const response = await apiClient.get<DurationPreference[]>('/api/v1/user-management/duration-preferences')
    if (response.error) {
      throw new Error(response.error)
    }
    return response.data || []
  },

  getGlobalByCategory: async (category: string): Promise<DurationPreference> => {
    const response = await apiClient.get<DurationPreference>(`/api/v1/user-management/duration-preferences/${category}`)
    if (response.error) {
      throw new Error(response.error)
    }
    return response.data!
  },

  createGlobal: async (prefs: DurationPreferenceCreate[]): Promise<DurationPreference[]> => {
    const response = await apiClient.post<DurationPreference[]>('/api/v1/user-management/duration-preferences', prefs)
    if (response.error) {
      throw new Error(response.error)
    }
    return response.data || []
  },

  updateGlobal: async (category: string, estimated_minutes: number, confidence?: number): Promise<DurationPreference> => {
    const response = await apiClient.put<DurationPreference>(
      `/api/v1/user-management/duration-preferences/${category}`,
      { estimated_minutes, confidence: confidence || 3 }
    )
    if (response.error) {
      throw new Error(response.error)
    }
    return response.data!
  },

  // Course-specific preferences
  getCoursePreferences: async (courseId: string): Promise<CourseDurationPreference[]> => {
    const response = await apiClient.get<CourseDurationPreference[]>(
      `/api/v1/user-management/course-duration-preferences/${courseId}`
    )
    if (response.error) {
      throw new Error(response.error)
    }
    return response.data || []
  },

  createCoursePreference: async (pref: CourseDurationPreferenceCreate): Promise<CourseDurationPreference> => {
    const response = await apiClient.post<CourseDurationPreference>(
      '/api/v1/user-management/course-duration-preferences',
      pref
    )
    if (response.error) {
      throw new Error(response.error)
    }
    return response.data!
  },

  deleteCoursePreference: async (courseId: string, category: string): Promise<void> => {
    const response = await apiClient.delete<{ status: string; message: string }>(
      `/api/v1/user-management/course-duration-preferences/${courseId}/${category}`
    )
    if (response.error) {
      throw new Error(response.error)
    }
  },
}

