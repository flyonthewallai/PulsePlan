import { apiClient } from '@/lib/api/client'

export interface Course {
  id: string
  user_id: string
  name: string
  color: string
  icon: string | null
  canvas_id: number | null
  canvas_name: string | null
  canvas_course_code: string | null
  external_source: string
  created_at: string
  updated_at: string
}

export const coursesApi = {
  list: async (): Promise<Course[]> => {
    const response = await apiClient.get<Course[]>('/api/v1/user-management/courses')
    if (response.error) {
      throw new Error(response.error)
    }
    return response.data || []
  },

  updateColor: async (courseId: string, color: string): Promise<Course> => {
    const response = await apiClient.patch<Course>(`/api/v1/user-management/courses/${courseId}`, { color })
    if (response.error) {
      throw new Error(response.error)
    }
    return response.data!
  },
}
