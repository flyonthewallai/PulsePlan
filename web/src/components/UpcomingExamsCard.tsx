import React, { useMemo, useState, useCallback, useRef, useEffect } from 'react'
import { GraduationCap, BookOpen, Clock, Calendar, X, Search, Loader2 } from 'lucide-react'
import { useTasks } from '../hooks/useTasks'
import { format, isToday, isTomorrow } from 'date-fns'
import type { Task } from '../lib/utils/types'

export function UpcomingExamsCard() {
  const [showModal, setShowModal] = useState(false)
  const [timeFilter, setTimeFilter] = useState<'week' | 'month' | 'all' | 'past'>('week')
  const [searchQuery, setSearchQuery] = useState('')
  
  const weekRef = useRef<HTMLButtonElement>(null);
  const monthRef = useRef<HTMLButtonElement>(null);
  const pastRef = useRef<HTMLButtonElement>(null);
  const allRef = useRef<HTMLButtonElement>(null);

  const [highlightStyle, setHighlightStyle] = useState({});

  const tabRefs = {
    week: weekRef,
    month: monthRef,
    past: pastRef,
    all: allRef,
  };

  useEffect(() => {
    const activeTabRef = tabRefs[timeFilter];
    if (activeTabRef.current) {
      setHighlightStyle({
        left: activeTabRef.current.offsetLeft,
        width: activeTabRef.current.offsetWidth,
      });
    }
  }, [timeFilter]);

  // Ensure highlight is positioned when modal opens
  useEffect(() => {
    if (showModal) {
      // Use a small delay to ensure DOM is fully rendered
      const timer = setTimeout(() => {
        const activeTabRef = tabRefs[timeFilter];
        if (activeTabRef.current) {
          setHighlightStyle({
            left: activeTabRef.current.offsetLeft,
            width: activeTabRef.current.offsetWidth,
          });
        }
      }, 10);
      
      return () => clearTimeout(timer);
    }
  }, [showModal, timeFilter]);
  
  // Enable real-time task updates
  const { data: allTasksData = [], isLoading, error } = useTasks()

  // Filter for quizzes and exams only
  const examTasks = useMemo(() => {
    return allTasksData.filter(task => {
      // Check task_type field
      const taskType = task.task_type?.toLowerCase()
      if (taskType === 'quiz' || taskType === 'exam') {
        return true
      }
      
      // Check title for exam/quiz keywords
      const title = task.title?.toLowerCase() || ''
      const examKeywords = [
        'exam', 'quiz', 'test', 'midterm', 'assessment', 
        'examination', 'mid-term', 'final exam', 'quiz exam',
        'unit test', 'chapter test', 'pop quiz', 'surprise quiz'
      ]
      
      return examKeywords.some(keyword => title.includes(keyword))
    })
  }, [allTasksData])

  // Process and sort exams based on time filter
  const { sortedCurrentExams, sortedPastExams } = useMemo(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    const endOfWeek = new Date(today)
    endOfWeek.setDate(endOfWeek.getDate() + 7)

    const endOfMonth = new Date(today)
    endOfMonth.setMonth(endOfMonth.getMonth() + 1)

    // Filter exams based on time filter
    let filteredExams = examTasks.filter(exam => {
      if (!exam.due_date) return false
      const examDate = new Date(exam.due_date)
      examDate.setHours(0, 0, 0, 0)
      
      switch (timeFilter) {
        case 'week':
          return examDate >= today && examDate <= endOfWeek
        case 'month':
          return examDate >= today && examDate <= endOfMonth
        case 'all':
          return examDate >= today
        case 'past':
          return examDate < today
        default:
          return examDate >= today && examDate <= endOfWeek
      }
    })

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filteredExams = filteredExams.filter(exam => 
        exam.title?.toLowerCase().includes(query) ||
        exam.courses?.canvas_course_code?.toLowerCase().includes(query)
      )
    }

    // Sort by due date
    const sorted = filteredExams.sort((a, b) => {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateA.getTime() - dateB.getTime()
    })

    // Split into current and past
    const current = sorted.filter(exam => {
      const examDate = new Date(exam.due_date)
      examDate.setHours(0, 0, 0, 0)
      return examDate >= today
    })

    const past = sorted.filter(exam => {
      const examDate = new Date(exam.due_date)
      examDate.setHours(0, 0, 0, 0)
      return examDate < today
    })

    return {
      sortedCurrentExams: current,
      sortedPastExams: past
    }
  }, [examTasks, timeFilter, searchQuery])

  // Get upcoming exams for card preview (this week + next week, max 4)
  const upcomingExams = useMemo(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    const endOfNextWeek = new Date(today)
    endOfNextWeek.setDate(endOfNextWeek.getDate() + 14) // This week + next week
    
    return examTasks.filter(exam => {
      if (!exam.due_date) return false
      const examDate = new Date(exam.due_date)
      examDate.setHours(0, 0, 0, 0)
      return examDate >= today && examDate <= endOfNextWeek
    }).sort((a, b) => {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateA.getTime() - dateB.getTime()
    }).slice(0, 4)
  }, [examTasks])

  // Format date for display
  const formatExamDate = (dueDate: string) => {
    const examDate = new Date(dueDate)
    
    if (isToday(examDate)) {
      return 'Today'
    } else if (isTomorrow(examDate)) {
      return 'Tomorrow'
    } else {
      return format(examDate, 'MMM d')
    }
  }

  // Format time for display
  const formatExamTime = (dueDate: string) => {
    const examDate = new Date(dueDate)
    return format(examDate, 'h:mm a')
  }

  // Get task color
  const getTaskColor = (task: Task) => {
    if (task.color) return task.color
    if (task.courses?.color) return task.courses.color
    return '#3B82F6' // Default blue
  }

  // Modal handlers
  const handleCardClick = useCallback(() => {
    setShowModal(true)
  }, [])

  const handleModalClose = useCallback(() => {
    setShowModal(false)
  }, [])

  const handleModalBackdropClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleModalClose()
    }
  }, [handleModalClose])

  if (isLoading) {
    return (
      <div className="w-full">
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4 min-h-[200px] flex flex-col">
          <div className="flex items-center justify-between mb-4 px-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
              UPCOMING EXAMS
            </span>
            <div className="w-4 h-4 flex items-center justify-center">
              <GraduationCap size={16} className="text-gray-400" />
            </div>
          </div>
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="w-8 h-8 bg-gray-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <Loader2 size={16} className="text-gray-400 animate-spin" />
              </div>
              <div className="text-sm font-medium text-gray-400 mb-1">
                Loading exams...
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
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4 min-h-[200px] flex flex-col">
          <div className="flex items-center justify-between mb-4 px-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
              UPCOMING EXAMS
            </span>
            <div className="w-4 h-4 flex items-center justify-center">
              <GraduationCap size={16} className="text-gray-400" />
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-4 h-4 rounded-full border-2 border-red-500 flex items-center justify-center mt-0.5">
                <X size={10} className="text-red-400" />
              </div>
              <div className="flex-1">
                <span className="text-sm font-medium text-red-400">
                  Error loading exams
                </span>
                <div className="text-xs text-gray-500 mt-1">
                  {error instanceof Error ? error.message : 'Failed to load exams'}
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
      <div 
        className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-5 h-full flex flex-col cursor-pointer hover:bg-neutral-800/60 transition-colors"
        onClick={handleCardClick}
      >
        <div className="flex items-center justify-between mb-4 px-1">
          <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
            UPCOMING EXAMS
          </span>
          <div className="w-4 h-4 flex items-center justify-center">
            <GraduationCap size={16} className="text-gray-400" />
          </div>
        </div>
        
        <div className="space-y-2.5 flex-1 flex flex-col">
          {upcomingExams.length > 0 ? (
            upcomingExams.map((exam) => (
              <div key={exam.id} className="flex items-start gap-3">
                {/* Exam type indicator */}
                <div 
                  className="w-2 h-2 rounded-full flex-shrink-0 mt-2"
                  style={{ backgroundColor: getTaskColor(exam) }}
                ></div>
                
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">
                    {exam.title}
                  </div>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    <div className="flex items-center gap-1">
                      <Calendar size={10} className="text-gray-400" />
                      <span className="text-xs text-gray-400">
                        {formatExamDate(exam.due_date)}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock size={10} className="text-gray-400" />
                      <span className="text-xs text-gray-400">
                        {formatExamTime(exam.due_date)}
                      </span>
                    </div>
                    {exam.courses?.canvas_course_code && (
                      <div className="flex items-center gap-1">
                        <BookOpen size={10} className="text-gray-400" />
                        <span className="text-xs text-gray-400">
                          {exam.courses.canvas_course_code}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-sm text-gray-400 text-center py-4">
              No upcoming exams
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      <div
        className={`fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300 cursor-default ${
          showModal ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={handleModalBackdropClick}
      >
        <div
          className={`border border-gray-700/50 w-full max-w-3xl rounded-xl h-[75vh] flex flex-col cursor-default transition-all duration-300 shadow-2xl ${
            showModal ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
          }`}
          style={{ backgroundColor: '#121212' }}
          onClick={(e) => e.stopPropagation()}
        >
          {showModal && (
            <>
              {/* Header - Matching Card Style */}
              <div className="p-5 border-b border-gray-700/30">
                {/* Title Row */}
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white tracking-tight">
                    Upcoming Exams
                  </h2>
                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      handleModalClose()
                    }}
                    className="p-1.5 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-neutral-800/60"
                    aria-label="Close modal"
                    type="button"
                  >
                    <X size={18} />
                  </button>
                </div>

                {/* Stats Bar - Clean Inline */}
                <div className="flex items-center gap-5 text-sm">
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-2xl font-bold text-white tabular-nums">
                      {timeFilter === 'past' ? sortedPastExams.length : sortedCurrentExams.length}
                    </span>
                    <span className="text-gray-400 font-medium">
                      {timeFilter === 'past' ? 'completed' : 'upcoming'}
                    </span>
                  </div>
                  <div className="h-3 w-px bg-gray-700/50"></div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-lg font-semibold text-white tabular-nums">
                      {sortedCurrentExams.length + sortedPastExams.length}
                    </span>
                    <span className="text-gray-400 font-medium">
                      {timeFilter === 'week' ? 'this week' :
                       timeFilter === 'month' ? 'this month' :
                       timeFilter === 'past' ? 'completed' :
                       'total'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Controls Bar - Clean Inline Layout */}
              <div className="px-5 py-3 border-b border-gray-700/30">
                <div className="flex items-center gap-3">
                  {/* Search Bar */}
                  <div className="relative flex-1">
                    <Search size={14} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search exams..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 rounded-lg bg-neutral-900/50 border border-gray-700/50 text-white placeholder-gray-500 focus:outline-none focus:border-gray-600 transition-colors text-sm"
                    />
                  </div>

                  {/* Time Filter Buttons - Sleek Segmented Control */}
                  <div className="relative flex rounded-lg p-1 bg-neutral-900/50 border border-gray-700/50">
                    <div
                      className="absolute top-1 bottom-1 bg-white rounded-md transition-all duration-300 ease-out shadow-sm"
                      style={highlightStyle}
                    />
                    <button
                      ref={weekRef}
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        setTimeFilter('week')
                      }}
                      className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                        timeFilter === 'week'
                          ? 'text-neutral-900'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Week
                    </button>
                    <button
                      ref={monthRef}
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        setTimeFilter('month')
                      }}
                      className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                        timeFilter === 'month'
                          ? 'text-neutral-900'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Month
                    </button>
                    <button
                      ref={allRef}
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        setTimeFilter('all')
                      }}
                      className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                        timeFilter === 'all'
                          ? 'text-neutral-900'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      All
                    </button>
                    <button
                      ref={pastRef}
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        setTimeFilter('past')
                      }}
                      className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                        timeFilter === 'past'
                          ? 'text-neutral-900'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Past
                    </button>
                  </div>
                </div>
              </div>

              {/* Exams list */}
              <div
                className="flex-1 overflow-y-auto px-5 py-3"
                style={{
                  scrollbarWidth: 'thin',
                  scrollbarColor: 'rgba(75, 85, 99, 0.3) transparent'
                }}
              >
                <div>
                  {/* Exams Section */}
                  {(() => {
                    let examsToShow = timeFilter === 'past' ? sortedPastExams : sortedCurrentExams
                    let showDateDividers = timeFilter !== 'past'

                    return examsToShow.length > 0 && (
                      <div className="space-y-2">
                        {examsToShow.map((exam, index) => {
                          const currentDate = exam.due_date ? new Date(exam.due_date).toDateString() : null
                          const previousDate = index > 0 && examsToShow[index - 1].due_date
                            ? new Date(examsToShow[index - 1].due_date).toDateString()
                            : null
                          const showDateDivider = showDateDividers && currentDate && currentDate !== previousDate

                          return (
                            <React.Fragment key={exam.id}>
                              {showDateDivider && (
                                <div className="flex items-center gap-3 py-3 first:pt-0">
                                  <div className="h-px bg-gray-700/50 flex-1"></div>
                                  <span className="text-xs font-semibold text-gray-400">
                                    {(() => {
                                      const examDate = new Date(exam.due_date)
                                      const today = new Date()
                                      today.setHours(0, 0, 0, 0)
                                      const tomorrow = new Date(today)
                                      tomorrow.setDate(tomorrow.getDate() + 1)

                                      if (examDate.toDateString() === today.toDateString()) {
                                        return 'Today'
                                      } else if (examDate.toDateString() === tomorrow.toDateString()) {
                                        return 'Tomorrow'
                                      } else {
                                        return examDate.toLocaleDateString('en-US', {
                                          weekday: 'short',
                                          month: 'short',
                                          day: 'numeric'
                                        })
                                      }
                                    })()}
                                  </span>
                                  <div className="h-px bg-gray-700/50 flex-1"></div>
                                </div>
                              )}
                              <div className="flex items-start gap-3 p-3 rounded-xl bg-neutral-800/40 border border-gray-700/50 hover:bg-neutral-800/50 transition-colors group">
                                <div
                                  className="w-2 h-2 rounded-full flex-shrink-0 mt-2"
                                  style={{ backgroundColor: getTaskColor(exam) }}
                                ></div>

                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between gap-3">
                                    <div className="text-base font-medium text-white">
                                      {exam.title}
                                    </div>
                                    <div className="flex items-center gap-2 flex-shrink-0">
                                      {exam.courses?.canvas_course_code && (
                                        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-neutral-800/50">
                                          <span className="text-xs font-medium text-gray-300">
                                            {exam.courses.canvas_course_code}
                                          </span>
                                        </div>
                                      )}
                                      <div className="flex items-center gap-1.5">
                                        <Calendar size={11} className="text-gray-500" />
                                        <span className="text-xs text-gray-400">
                                          {formatExamDate(exam.due_date)}
                                        </span>
                                      </div>
                                      <div className="flex items-center gap-1.5">
                                        <Clock size={11} className="text-gray-500" />
                                        <span className="text-xs text-gray-400">
                                          {formatExamTime(exam.due_date)}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </React.Fragment>
                          )
                        })}
                      </div>
                    )
                  })()}

                  {/* No exams message */}
                  {(() => {
                    let examsToShow = timeFilter === 'past' ? sortedPastExams : sortedCurrentExams
                    let message = ''
                    let subMessage = ''

                    // Check if there's an active search query first
                    if (searchQuery.trim()) {
                      message = `No results for "${searchQuery}"`
                      subMessage = 'Try a different search term'
                    } else {
                      // No search query - show filter-specific messages
                      if (timeFilter === 'past') {
                        message = 'No completed exams'
                        subMessage = 'All caught up!'
                      } else if (timeFilter === 'week') {
                        message = 'No exams this week'
                        subMessage = 'Looking good!'
                      } else if (timeFilter === 'month') {
                        message = 'No exams this month'
                        subMessage = 'Looking good!'
                      } else {
                        message = 'No upcoming exams'
                        subMessage = 'All caught up!'
                      }
                    }

                    return examsToShow.length === 0 && (
                      <div className="text-center py-16">
                        <div className="text-sm font-medium text-gray-400 mb-1">
                          {message}
                        </div>
                        <div className="text-xs text-gray-500">
                          {subMessage}
                        </div>
                      </div>
                    )
                  })()}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
