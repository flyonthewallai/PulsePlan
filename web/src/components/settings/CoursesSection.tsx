import { useEffect, useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { cn } from '../../lib/utils'
import { coursesApi, type Course } from '../../services/user'
import { formatCourseCode } from '../../lib/utils/formatters'
import { CourseDurationPreferencesSection } from './CourseDurationPreferencesSection'

interface CoursesSectionProps {
  onCoursePress?: (course: Course) => void
}

export function CoursesSection({ onCoursePress }: CoursesSectionProps) {
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [courses, setCourses] = useState<Course[]>([])
  const [coursesLoading, setCoursesLoading] = useState(false)

  const fetchCourses = async (signal?: AbortSignal) => {
    try {
      setCoursesLoading(true)
      const data = await coursesApi.list()
      if (!signal?.aborted) {
        setCourses(data)
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }
      if (!signal?.aborted) {
        console.error('Failed to fetch courses:', error)
      }
    } finally {
      if (!signal?.aborted) {
        setCoursesLoading(false)
      }
    }
  }

  useEffect(() => {
    const abortController = new AbortController()
    fetchCourses(abortController.signal)
    
    return () => {
      abortController.abort()
    }
  }, [])

  const handleCourseClick = (course: Course) => {
    setSelectedCourse(course)
    if (onCoursePress) {
      onCoursePress(course)
    }
  }

  const handleBack = () => {
    setSelectedCourse(null)
  }

  // Show course detail view if a course is selected
  if (selectedCourse) {
    return (
      <CourseDurationPreferencesSection
        course={selectedCourse}
        onBack={handleBack}
      />
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-gray-400 text-sm mb-3">
        Manage your courses and customize their colors and duration preferences. These will be used to organize your assignments and schedule.
      </p>

      {coursesLoading ? (
        <div className="flex items-center justify-center py-12">
          <p className="text-gray-400">Loading courses...</p>
        </div>
      ) : courses.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <p className="text-gray-400">No courses found. Sync your Canvas account to import courses.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {courses.map((course) => (
            <button
              key={course.id}
              onClick={() => handleCourseClick(course)}
              className="w-full rounded-lg p-3 flex items-center justify-between transition-colors bg-neutral-800/40 border border-gray-700/50 hover:bg-neutral-800/60"
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-5 h-5 rounded-full"
                  style={{ backgroundColor: course.color }}
                />
                <span className="text-sm font-semibold text-white">
                  {course.canvas_course_code ? formatCourseCode(course.canvas_course_code) : course.name}
                </span>
              </div>
              <ChevronRight size={16} className="text-gray-400" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

