import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  X,
  User,
  Settings,
  Calendar,
  HelpCircle,
  ExternalLink,
  RefreshCw,
  Mail,
  Bell,
  School,
  Clock,
  Star,
  BookOpen,
  Tag as TagIcon,
  Newspaper,
  BrainCircuit,
  Sparkles,
  Timer,
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { typography, spacing, components } from '../../lib/design-tokens'
import { CourseColorPicker } from './CourseColorPicker'
import { coursesApi, type Course } from '../../services/user'
import { useProfile } from '@/hooks/profile'
import type { SettingsSection } from '../settings/types'
import {
  ProfileSection,
  AppearanceSection,
  RemindersSection,
  BriefingsSection,
  CoursesSection,
  TagsSection,
  HobbiesSection,
  WeeklyPulseSection,
  StudySection,
  PersonalizationSection,
  PremiumSection,
  DurationPreferencesSection,
} from '../settings'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  initialSection?: SettingsSection
}

export function SettingsModal({ isOpen, onClose, initialSection = 'profile' }: SettingsModalProps) {
  const navigate = useNavigate()
  const [activeSection, setActiveSection] = useState<SettingsSection>(initialSection)
  
  useEffect(() => {
    if (isOpen) {
      setActiveSection(initialSection || 'profile')
    }
  }, [isOpen, initialSection])

  const { data: profile } = useProfile()

  // Profile state
  const [fullName, setFullName] = useState('')
  const [school, setSchool] = useState('')
  const [academicYear, setAcademicYear] = useState('')

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || '')
      setSchool(profile.school || '')
      setAcademicYear(profile.academic_year || '')
    }
  }, [profile])

  // Briefings settings
  const [isBriefingsEnabled, setIsBriefingsEnabled] = useState(true)
  const [scheduleContent, setScheduleContent] = useState('Show me today\'s schedule with time blocks, priorities, and any potential conflicts or gaps.')
  const [suggestionsContent, setSuggestionsContent] = useState('Provide AI-powered recommendations for optimizing my day, including schedule adjustments and productivity tips.')
  const [motivationContent, setMotivationContent] = useState('Include a brief motivational message or academic tip to start my day with focus and energy.')
  const [remindersContent, setRemindersContent] = useState('Highlight important deadlines, upcoming assignments, and tasks that need my attention today.')

  // Weekly Pulse settings
  const [isWeeklyPulseEnabled, setIsWeeklyPulseEnabled] = useState(true)
  const [weeklyPulseDay, setWeeklyPulseDay] = useState<'sunday' | 'monday' | 'friday'>('sunday')
  const [upcomingTasksContent, setUpcomingTasksContent] = useState('Show me my most important deadlines and assignments for the upcoming week, prioritized by due date and impact on my academic goals.')
  const [overdueItemsContent, setOverdueItemsContent] = useState('List any overdue tasks or assignments that need immediate attention, along with suggestions for catching up.')
  const [studyHabitsContent, setStudyHabitsContent] = useState('Provide insights into my study patterns, productivity trends, and time management effectiveness from the past week.')
  const [streaksContent, setStreaksContent] = useState('Highlight my current streaks, recent achievements, and progress toward personal and academic milestones.')
  const [optionalPulseContent, setOptionalPulseContent] = useState('')

  // Study settings
  const [studyStartHour, setStudyStartHour] = useState(9)
  const [studyEndHour, setStudyEndHour] = useState(17)

  // Reminders settings
  const [isTaskRemindersEnabled, setIsTaskRemindersEnabled] = useState(true)
  const [isMissedSummaryEnabled, setIsMissedSummaryEnabled] = useState(true)
  const [isEmailEnabled, setIsEmailEnabled] = useState(false)
  const [isInAppEnabled, setIsInAppEnabled] = useState(true)
  const [isPushEnabled, setIsPushEnabled] = useState(false)

  // Personalization
  const [agentInstructions, setAgentInstructions] = useState('')
  const [agentMemories, setAgentMemories] = useState('')

  // Courses
  const [showColorPicker, setShowColorPicker] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)

  const handleCoursePress = (course: Course) => {
    setSelectedCourse(course)
    setShowColorPicker(true)
  }

  const handleColorSelect = async (color: string) => {
    if (!selectedCourse) return
    try {
      await coursesApi.updateColor(selectedCourse.id, color)
      setSelectedCourse(null)
      setShowColorPicker(false)
    } catch (error) {
      console.error('Failed to update course color:', error)
    }
  }

  const saveProfile = async () => {
    // Profile saving is handled in ProfileSection
  }

  const navigationItems: { id: SettingsSection; label: string; icon: any }[] = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'premium', label: 'Premium', icon: Sparkles },
    { id: 'personalization', label: 'Personalization', icon: BrainCircuit },
    { id: 'reminders', label: 'Reminders', icon: Clock },
    { id: 'appearance', label: 'Appearance', icon: Settings },
    { id: 'briefings', label: 'Briefings', icon: Newspaper },
    { id: 'weekly-pulse', label: 'Weekly Pulse', icon: Mail },
    { id: 'hobbies', label: 'Hobbies', icon: Star },
    { id: 'study', label: 'Study', icon: BookOpen },
    { id: 'duration-preferences', label: 'Duration Preferences', icon: Timer },
    { id: 'courses', label: 'Courses', icon: School },
    { id: 'tags', label: 'Tags', icon: TagIcon },
  ]

  if (!isOpen) return null

  const renderSettingsContent = () => {
    switch (activeSection) {
      case 'profile':
        return <ProfileSection />
      case 'appearance':
        return <AppearanceSection />
      case 'reminders':
        return (
          <RemindersSection
            isTaskRemindersEnabled={isTaskRemindersEnabled}
            setIsTaskRemindersEnabled={setIsTaskRemindersEnabled}
            isMissedSummaryEnabled={isMissedSummaryEnabled}
            setIsMissedSummaryEnabled={setIsMissedSummaryEnabled}
            isEmailEnabled={isEmailEnabled}
            setIsEmailEnabled={setIsEmailEnabled}
            isInAppEnabled={isInAppEnabled}
            setIsInAppEnabled={setIsInAppEnabled}
            isPushEnabled={isPushEnabled}
            setIsPushEnabled={setIsPushEnabled}
          />
        )
      case 'briefings':
        return (
          <BriefingsSection
            isBriefingsEnabled={isBriefingsEnabled}
            setIsBriefingsEnabled={setIsBriefingsEnabled}
            scheduleContent={scheduleContent}
            setScheduleContent={setScheduleContent}
            suggestionsContent={suggestionsContent}
            setSuggestionsContent={setSuggestionsContent}
            motivationContent={motivationContent}
            setMotivationContent={setMotivationContent}
            remindersContent={remindersContent}
            setRemindersContent={setRemindersContent}
          />
        )
      case 'duration-preferences':
        return <DurationPreferencesSection />
      case 'courses':
        return <CoursesSection onCoursePress={handleCoursePress} />
      case 'tags':
        return <TagsSection />
      case 'hobbies':
        return <HobbiesSection />
      case 'weekly-pulse':
        return (
          <WeeklyPulseSection
            isWeeklyPulseEnabled={isWeeklyPulseEnabled}
            setIsWeeklyPulseEnabled={setIsWeeklyPulseEnabled}
            weeklyPulseDay={weeklyPulseDay}
            setWeeklyPulseDay={setWeeklyPulseDay}
            upcomingTasksContent={upcomingTasksContent}
            setUpcomingTasksContent={setUpcomingTasksContent}
            overdueItemsContent={overdueItemsContent}
            setOverdueItemsContent={setOverdueItemsContent}
            studyHabitsContent={studyHabitsContent}
            setStudyHabitsContent={setStudyHabitsContent}
            streaksContent={streaksContent}
            setStreaksContent={setStreaksContent}
            optionalPulseContent={optionalPulseContent}
            setOptionalPulseContent={setOptionalPulseContent}
          />
        )
      case 'study':
        return (
          <StudySection
            studyStartHour={studyStartHour}
            setStudyStartHour={setStudyStartHour}
            studyEndHour={studyEndHour}
            setStudyEndHour={setStudyEndHour}
          />
        )
      case 'personalization':
        return (
          <PersonalizationSection
            agentInstructions={agentInstructions}
            setAgentInstructions={setAgentInstructions}
            agentMemories={agentMemories}
            setAgentMemories={setAgentMemories}
            onSaveProfile={saveProfile}
          />
        )
      case 'premium':
        return <PremiumSection />
      default:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">
                {navigationItems.find(item => item.id === activeSection)?.label}
              </h3>
              <p className="text-gray-400">
                Settings for {navigationItems.find(item => item.id === activeSection)?.label.toLowerCase()} coming soon.
              </p>
            </div>
          </div>
        )
    }
  }

  return (
    <div className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 transition-all duration-300 ${
      isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
    }`}>
      <div className={cn(
        'bg-[#121212] border border-gray-700/50 rounded-2xl w-full max-w-3xl h-[75vh] flex overflow-hidden transition-all duration-300',
        isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
      )}>
        {isOpen ? (
          <>
            {/* Left Sidebar */}
            <div className="w-56 flex flex-col border-r border-gray-700/50 bg-[#121212]">
              {/* Logo */}
              <div className="px-4 py-4">
                <div className="flex items-center gap-3">
                  <img
                    src="/pulse.png"
                    alt="PulsePlan"
                    className="w-8 h-8 rounded-lg"
                  />
                  <span className={cn(typography.sectionTitle, "text-white")}>PulsePlan</span>
                </div>
              </div>

              {/* Navigation */}
              <nav className="flex-1 px-4 py-3 space-y-1">
                {navigationItems.map((item) => {
                  const Icon = item.icon
                  const isActive = activeSection === item.id
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveSection(item.id)}
                      className={cn(
                        "w-full flex items-center px-3 py-2 rounded-lg text-left transition-all duration-150 ease-out",
                        isActive 
                          ? "text-white font-semibold hover:bg-neutral-700/40" 
                          : "text-gray-400 hover:text-white hover:bg-neutral-700/40"
                      )}
                    >
                      <Icon size={18} className="flex-shrink-0" />
                      <span className="text-sm whitespace-nowrap ml-2">{item.label}</span>
                    </button>
                  )
                })}
              </nav>

              {/* Help Link */}
              <div className="px-4 py-3">
                <a
                  href="#"
                  className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:text-white hover:bg-neutral-700/40 rounded-lg transition-all duration-150 ease-out"
                >
                  <HelpCircle size={18} />
                  <span className="text-sm font-medium">Get help</span>
                  <ExternalLink size={14} className="ml-auto" />
                </a>
              </div>
            </div>

            {/* Right Content */}
            <div className="flex-1 flex flex-col">
              {/* Header */}
              <div className={spacing.modal.header}>
                <div className="flex items-center justify-between">
                  <h2 className={components.modal.title}>
                    {navigationItems.find(item => item.id === activeSection)?.label || 'Settings'}
                  </h2>
                  <div className="flex items-center gap-2">
                    {(activeSection === 'courses' || activeSection === 'tags') && (
                      <button
                        onClick={() => {
                          // Refresh handled in section components
                        }}
                        className={components.modal.closeButton}
                        title={activeSection === 'courses' ? 'Refresh courses' : 'Refresh tags'}
                      >
                        <RefreshCw size={16} />
                      </button>
                    )}
                    <button
                      onClick={onClose}
                      className={components.modal.closeButton}
                    >
                      <X size={18} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className={cn(spacing.modal.content, "flex-1 overflow-y-auto")}>
                {renderSettingsContent()}
              </div>
            </div>

            {/* Course Color Picker */}
            <CourseColorPicker
              visible={showColorPicker}
              onClose={() => {
                setShowColorPicker(false)
                setSelectedCourse(null)
              }}
              onSelectColor={handleColorSelect}
              currentColor={selectedCourse?.color || '#6366F1'}
              courseName={selectedCourse?.canvas_course_code || selectedCourse?.name || ''}
            />
          </>
        ) : null}
      </div>
    </div>
  )
}
