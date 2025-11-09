import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  X,
  User,
  Settings,
  Calendar,
  HelpCircle,
  ExternalLink,
  ChevronRight,
  Mail,
  Bell,
  Smartphone,
  School,
  Clock,
  Star,
  BookOpen,
  RefreshCw,
  Tag as TagIcon,
  Plus,
  Trash2,
  Newspaper,
  BrainCircuit,
  Info,
  Music,
  Camera,
  Book,
  Gamepad2,
  Palette,
  Target,
  Dumbbell,
  Bike,
  Coffee,
  Film,
  Heart,
  Users,
  MountainSnow,
  Mountain,
  Snowflake,
  Sun,
  Moon,
  Pen,
  Sparkles,
  Check,
} from 'lucide-react'
import { cn } from '../lib/utils'
import { typography, colors, spacing, components, cn as cnTokens } from '../lib/design-tokens'
import { CourseColorPicker } from './CourseColorPicker'
import { coursesApi, type Course } from '../services/coursesService'
import { tagsApi, type Tag } from '../services/tagsService'
import { useProfile, useUpdateProfile } from '../hooks/useProfile'
import { useSendTestBriefing } from '../hooks/useBriefing'
import { AddHobbyPrompt } from './AddHobbyPrompt'
import { HobbySummary } from './HobbySummary'
import { hobbiesApi, type Hobby as HobbyAPI, type CreateHobbyRequest } from '../lib/api/sdk'
import { useHobbies, useCreateHobby, useUpdateHobby, useDeleteHobby } from '../hooks/useHobbies'
import { profileSettingsSchema, tagCreationSchema, hobbySettingsSchema, validateInput } from '../lib/validation/settings'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  initialSection?: SettingsSection
}

type SettingsSection = 'profile' | 'appearance' | 'briefings' | 'hobbies' | 'reminders' | 'study' | 'courses' | 'tags' | 'weekly-pulse' | 'personalization' | 'premium'

export function SettingsModal({ isOpen, onClose, initialSection = 'profile' }: SettingsModalProps) {
  const navigate = useNavigate()
  const [activeSection, setActiveSection] = useState<SettingsSection>(initialSection)
  
  // Update activeSection when modal opens or initialSection prop changes
  useEffect(() => {
    if (isOpen) {
      setActiveSection(initialSection || 'profile')
    }
  }, [isOpen, initialSection])

  // Profile data with React Query
  const { data: profile, isLoading: profileLoading } = useProfile()
  const updateProfileMutation = useUpdateProfile()

  // Briefing mutation
  const sendTestBriefingMutation = useSendTestBriefing()
  const [testBriefingStatus, setTestBriefingStatus] = useState<string | null>(null)

  // Local state for form inputs
  const [fullName, setFullName] = useState('')
  const [school, setSchool] = useState('')
  const [academicYear, setAcademicYear] = useState('')

  // Sync form state with profile data
  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || '')
      setSchool(profile.school || '')
      setAcademicYear(profile.academic_year || '')
    }
  }, [profile])

  // Briefings settings
  const [isBriefingsEnabled, setIsBriefingsEnabled] = useState(true)
  const [isTaskRemindersEnabled, setIsTaskRemindersEnabled] = useState(true)
  const [isMissedSummaryEnabled, setIsMissedSummaryEnabled] = useState(true)
  const [isEmailEnabled, setIsEmailEnabled] = useState(false)
  const [isInAppEnabled, setIsInAppEnabled] = useState(true)
  const [isPushEnabled, setIsPushEnabled] = useState(false)
  const [scheduleContent, setScheduleContent] = useState('Show me today\'s schedule with time blocks, priorities, and any potential conflicts or gaps.')
  const [suggestionsContent, setSuggestionsContent] = useState('Provide AI-powered recommendations for optimizing my day, including schedule adjustments and productivity tips.')
  const [motivationContent, setMotivationContent] = useState('Include a brief motivational message or academic tip to start my day with focus and energy.')
  const [remindersContent, setRemindersContent] = useState('Highlight important deadlines, upcoming assignments, and tasks that need my attention today.')

  // Weekly Pulse settings
  const [isWeeklyPulseEnabled, setIsWeeklyPulseEnabled] = useState(true)
  const [weeklyPulseDay, setWeeklyPulseDay] = useState<'sunday' | 'monday' | 'friday'>('sunday')
  const [showDaySelection, setShowDaySelection] = useState(false)
  const [upcomingTasksContent, setUpcomingTasksContent] = useState('Show me my most important deadlines and assignments for the upcoming week, prioritized by due date and impact on my academic goals.')
  const [overdueItemsContent, setOverdueItemsContent] = useState('List any overdue tasks or assignments that need immediate attention, along with suggestions for catching up.')
  const [studyHabitsContent, setStudyHabitsContent] = useState('Provide insights into my study patterns, productivity trends, and time management effectiveness from the past week.')
  const [streaksContent, setStreaksContent] = useState('Highlight my current streaks, recent achievements, and progress toward personal and academic milestones.')
  const [optionalPulseContent, setOptionalPulseContent] = useState('')

  // Study settings
  const [studyStartHour, setStudyStartHour] = useState(9)
  const [studyEndHour, setStudyEndHour] = useState(17)

  // Courses settings
  const [courses, setCourses] = useState<Course[]>([])
  const [coursesLoading, setCoursesLoading] = useState(false)
  const [showColorPicker, setShowColorPicker] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)

  // Tags settings
  const [tags, setTags] = useState<Tag[]>([])
  const [tagsLoading, setTagsLoading] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const [isCreatingTag, setIsCreatingTag] = useState(false)

  // Personalization (Agent Instructions + Memories)
  const [agentInstructions, setAgentInstructions] = useState('')
  const [agentMemories, setAgentMemories] = useState('')
  const [personalizationSavedAt, setPersonalizationSavedAt] = useState<string | null>(null)

  // Hobbies state - using React Query hooks
  const { data: hobbies = [], isLoading: isLoadingHobbies } = useHobbies()
  const createHobbyMutation = useCreateHobby()
  const updateHobbyMutation = useUpdateHobby()
  const deleteHobbyMutation = useDeleteHobby()

  type Hobby = HobbyAPI & {
    // Add local-only fields if needed
  }

  const [selectedHobby, setSelectedHobby] = useState<Partial<Hobby> | null>(null)
  const [showHobbyModal, setShowHobbyModal] = useState(false)

  // New conversational hobby input state
  const [showAddHobbyPrompt, setShowAddHobbyPrompt] = useState(false)
  const [showHobbySummary, setShowHobbySummary] = useState(false)
  const [parsedHobby, setParsedHobby] = useState<any>(null)
  const [hobbyConfidence, setHobbyConfidence] = useState(1.0)
  const [isParsingHobby, setIsParsingHobby] = useState(false)

  const getHobbyIcon = (icon: Hobby['icon'], className?: string) => {
    const props = { size: 16, className: cn('text-gray-400', className) }
    switch (icon) {
      case 'Music': return <Music {...props} />
      case 'Camera': return <Camera {...props} />
      case 'Book': return <Book {...props} />
      case 'Gamepad2': return <Gamepad2 {...props} />
      case 'Palette': return <Palette {...props} />
      case 'Dumbbell': return <Dumbbell {...props} />
      case 'Bike': return <Bike {...props} />
      case 'Coffee': return <Coffee {...props} />
      case 'Film': return <Film {...props} />
      case 'Heart': return <Heart {...props} />
      case 'Users': return <Users {...props} />
      case 'Snowflake': return <Snowflake {...props} />
      case 'MountainSnow': return <MountainSnow {...props} />
      case 'Mountain': return <Mountain {...props} />
      default: return <Target {...props} />
    }
  }

  // New conversational flow handlers
  const handleAddHobby = () => {
    setShowAddHobbyPrompt(true)
  }

  const handleHobbyDescriptionSubmit = async (description: string) => {
    setIsParsingHobby(true)
    try {
      const result = await hobbiesApi.parseHobby(description)
      if (result.success && result.hobby) {
        setParsedHobby(result.hobby)
        setHobbyConfidence(result.confidence)
        setShowAddHobbyPrompt(false)
        setShowHobbySummary(true)
      } else {
        alert(result.error || 'Failed to parse hobby description')
      }
    } catch (error) {
      console.error('Error parsing hobby:', error)
      alert('Failed to parse hobby description. Please try again.')
    } finally {
      setIsParsingHobby(false)
    }
  }

  const handleHobbyConfirm = async () => {
    if (!parsedHobby) return
    try {
      await createHobbyMutation.mutateAsync({
        name: parsedHobby.name,
        icon: parsedHobby.icon,
        preferred_time: parsedHobby.preferred_time,
        specific_time: parsedHobby.specific_time,
        days: parsedHobby.days,
        duration_min: parsedHobby.duration.min,
        duration_max: parsedHobby.duration.max,
        flexibility: parsedHobby.flexibility,
        notes: parsedHobby.notes,
      })
      setShowHobbySummary(false)
      setParsedHobby(null)
    } catch (error) {
      console.error('Error creating hobby:', error)
      alert('Failed to save hobby. Please try again.')
    }
  }

  const handleHobbyEdit = () => {
    if (!parsedHobby) return
    // Convert parsed hobby to editable format
    setSelectedHobby({
      name: parsedHobby.name,
      icon: parsedHobby.icon,
      preferred_time: parsedHobby.preferred_time,
      specific_time: parsedHobby.specific_time,
      days: parsedHobby.days,
      duration_min: parsedHobby.duration.min,
      duration_max: parsedHobby.duration.max,
      flexibility: parsedHobby.flexibility,
      notes: parsedHobby.notes,
    })
    setShowHobbySummary(false)
    setShowHobbyModal(true)
  }

  const handleEditHobby = (h: Hobby) => {
    setSelectedHobby(h)
    setShowHobbyModal(true)
  }

  const handleSaveHobby = async () => {
    if (!selectedHobby) return
    try {
      if (selectedHobby.id) {
        // Update existing hobby
        await updateHobbyMutation.mutateAsync({
          id: selectedHobby.id,
          updates: {
            name: selectedHobby.name!,
            icon: selectedHobby.icon!,
            preferred_time: selectedHobby.preferred_time!,
            specific_time: selectedHobby.specific_time,
            days: selectedHobby.days!,
            duration_min: selectedHobby.duration_min!,
            duration_max: selectedHobby.duration_max!,
            flexibility: selectedHobby.flexibility!,
            notes: selectedHobby.notes!,
          },
        })
      } else {
        // Create new hobby
        await createHobbyMutation.mutateAsync({
          name: selectedHobby.name!,
          icon: selectedHobby.icon!,
          preferred_time: selectedHobby.preferred_time!,
          specific_time: selectedHobby.specific_time,
          days: selectedHobby.days!,
          duration_min: selectedHobby.duration_min!,
          duration_max: selectedHobby.duration_max!,
          flexibility: selectedHobby.flexibility!,
          notes: selectedHobby.notes || '',
        })
      }
      setShowHobbyModal(false)
      setSelectedHobby(null)
    } catch (error) {
      console.error('Error saving hobby:', error)
      alert('Failed to save hobby. Please try again.')
    }
  }

  const handleDeleteHobby = async (id: string) => {
    if (!confirm('Are you sure you want to delete this hobby?')) return
    try {
      await deleteHobbyMutation.mutateAsync({ id })
    } catch (error) {
      console.error('Error deleting hobby:', error)
      alert('Failed to delete hobby. Please try again.')
    }
  }

  // Fetch courses when courses section is active
  useEffect(() => {
    if (isOpen && activeSection === 'courses') {
      const abortController = new AbortController()
      fetchCourses(abortController.signal)
      
      return () => {
        abortController.abort()
      }
    }
  }, [isOpen, activeSection])

  // Fetch tags when tags section is active
  useEffect(() => {
    if (isOpen && activeSection === 'tags') {
      const abortController = new AbortController()
      fetchTags(abortController.signal)
      
      return () => {
        abortController.abort()
      }
    }
  }, [isOpen, activeSection])

  const saveProfile = async () => {
    try {
      // Validate input before submitting
      const validation = validateInput(profileSettingsSchema, {
        fullName,
        school,
        academicYear,
      })
      
      if (!validation.success) {
        alert(validation.error)
        return
      }
      
      await updateProfileMutation.mutateAsync({
        full_name: validation.data.fullName,
        school: validation.data.school,
        academic_year: validation.data.academicYear,
      })
      console.log('Profile updated successfully')
    } catch (error) {
      console.error('Error updating profile:', error)
      alert('Failed to update profile. Please try again.')
    }
  }

  const handleSendTestBriefing = async () => {
    try {
      setTestBriefingStatus('sending')
      const result = await sendTestBriefingMutation.mutateAsync({
        send_email: true,
        send_notification: false
      })
      if (result.success) {
        setTestBriefingStatus('success')
        setTimeout(() => setTestBriefingStatus(null), 5000)
      } else {
        setTestBriefingStatus('error')
        setTimeout(() => setTestBriefingStatus(null), 5000)
      }
    } catch (error) {
      console.error('Error sending test briefing:', error)
      setTestBriefingStatus('error')
      setTimeout(() => setTestBriefingStatus(null), 5000)
    }
  }

  const fetchCourses = async (signal?: AbortSignal) => {
    try {
      setCoursesLoading(true)
      const data = await coursesApi.list()
      // Check if aborted before updating state
      if (!signal?.aborted) {
        setCourses(data)
      }
    } catch (error) {
      // Ignore abort errors
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

  const handleCoursePress = (course: Course) => {
    setSelectedCourse(course)
    setShowColorPicker(true)
  }

  const handleColorSelect = async (color: string) => {
    if (!selectedCourse) return

    try {
      await coursesApi.updateColor(selectedCourse.id, color)
      // Update local state
      setCourses(courses.map(c =>
        c.id === selectedCourse.id ? { ...c, color } : c
      ))
    } catch (error) {
      console.error('Failed to update course color:', error)
    }
  }

  const fetchTags = async (signal?: AbortSignal) => {
    try {
      setTagsLoading(true)
      const data = await tagsApi.getAllTags()
      // Check if aborted before updating state
      if (!signal?.aborted) {
        setTags(data)
      }
    } catch (error) {
      // Ignore abort errors
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }
      if (!signal?.aborted) {
        console.error('Failed to fetch tags:', error)
      }
    } finally {
      if (!signal?.aborted) {
        setTagsLoading(false)
      }
    }
  }

  // Persist personalization to backend profile for now (simple fields)
  const savePersonalization = async () => {
    try {
      await updateProfileMutation.mutateAsync({
        agent_instructions: agentInstructions,
        agent_memories: agentMemories,
      } as any)
      setPersonalizationSavedAt(new Date().toISOString())
    } catch (e) {
      console.error('Failed saving personalization', e)
      alert('Failed to save. Please try again.')
    }
  }

  const handleCreateTag = async () => {
    // Validate tag name before submitting
    const validation = validateInput(tagCreationSchema, {
      name: newTagName,
    })
    
    if (!validation.success) {
      alert(validation.error)
      return
    }

    try {
      setIsCreatingTag(true)
      await tagsApi.createUserTag(validation.data.name)
      setNewTagName('')
      await fetchTags() // Refresh the list
    } catch (error: unknown) {
      console.error('Failed to create tag:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create tag'
      alert(errorMessage)
    } finally {
      setIsCreatingTag(false)
    }
  }

  const handleDeleteTag = async (tag: Tag) => {
    if (tag.type !== 'user') return
    
    if (!confirm(`Are you sure you want to delete the "${tag.name}" tag?`)) {
      return
    }

    try {
      // If no ID, we need to look it up or delete by name
      if (tag.id) {
        await tagsApi.deleteUserTag(tag.id)
      } else {
        // Fallback: find and delete by name
        await tagsApi.deleteUserTagByName(tag.name)
      }
      await fetchTags() // Refresh the list
    } catch (error) {
      console.error('Failed to delete tag:', error)
      alert('Failed to delete tag')
    }
  }

  // Navigation items (add Personalization)
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
    { id: 'courses', label: 'Courses', icon: School },
    { id: 'tags', label: 'Tags', icon: TagIcon },
  ]

  const formatCourseCode = (courseCode: string): string => {
    // Extract text and first 4 numbers from course code (same as TasksCard)
    const match = courseCode.match(/^([A-Za-z]+)\s*(\d{4})/)
    if (match) {
      return `${match[1]} ${match[2]}`
    }

    // Try 3-digit numbers
    const match3 = courseCode.match(/^([A-Za-z]+)\s*(\d{3})/)
    if (match3) {
      return `${match3[1]} ${match3[2]}`
    }

    // If no match, return as-is
    return courseCode
  }

  if (!isOpen) return null

  const renderSettingsContent = () => {
    switch (activeSection) {
      case 'reminders':
        return (
          <div className="space-y-6">
            <p className="text-gray-400 text-sm">Configure your notification preferences and delivery methods</p>

            {/* Task Reminders */}
            <div>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Task Reminders</h3>
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden divide-y divide-gray-700/40">
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Bell size={18} className="text-gray-400" />
                    <div>
                      <div className="text-white text-sm font-medium">Task Reminders</div>
                      <div className="text-xs text-gray-400">Get notified before tasks are due</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsTaskRemindersEnabled(!isTaskRemindersEnabled)}
                    className={cn(
                      "w-10 h-5 rounded-full transition-colors",
                      isTaskRemindersEnabled ? "bg-blue-500" : "bg-gray-600"
                    )}
                  >
                    <div
                      className={cn(
                        "w-4 h-4 bg-white rounded-full transition-transform",
                        isTaskRemindersEnabled ? "translate-x-5" : "translate-x-0.5"
                      )}
                    />
                  </button>
                </div>
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Calendar size={18} className="text-gray-400" />
                    <div>
                      <div className="text-white text-sm font-medium">Missed Task Summary</div>
                      <div className="text-xs text-gray-400">Daily summary of incomplete tasks</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsMissedSummaryEnabled(!isMissedSummaryEnabled)}
                    className={cn(
                      "w-10 h-5 rounded-full transition-colors",
                      isMissedSummaryEnabled ? "bg-blue-500" : "bg-gray-600"
                    )}
                  >
                    <div
                      className={cn(
                        "w-4 h-4 bg-white rounded-full transition-transform",
                        isMissedSummaryEnabled ? "translate-x-5" : "translate-x-0.5"
                      )}
                    />
                  </button>
                </div>
              </div>
            </div>

            {/* Delivery Methods */}
            <div>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Delivery Methods</h3>
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden divide-y divide-gray-700/40">
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Mail size={18} className="text-gray-400" />
                    <div>
                      <div className="text-white text-sm font-medium">Email</div>
                      <div className="text-xs text-gray-400">Receive notifications via email</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsEmailEnabled(!isEmailEnabled)}
                    className={cn(
                      "w-10 h-5 rounded-full transition-colors",
                      isEmailEnabled ? "bg-blue-500" : "bg-gray-600"
                    )}
                  >
                    <div
                      className={cn(
                        "w-4 h-4 bg-white rounded-full transition-transform",
                        isEmailEnabled ? "translate-x-5" : "translate-x-0.5"
                      )}
                    />
                  </button>
                </div>
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Bell size={18} className="text-gray-400" />
                    <div>
                      <div className="text-white text-sm font-medium">In‑App</div>
                      <div className="text-xs text-gray-400">Show notifications within the app</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsInAppEnabled(!isInAppEnabled)}
                    className={cn(
                      "w-10 h-5 rounded-full transition-colors",
                      isInAppEnabled ? "bg-blue-500" : "bg-gray-600"
                    )}
                  >
                    <div
                      className={cn(
                        "w-4 h-4 bg-white rounded-full transition-transform",
                        isInAppEnabled ? "translate-x-5" : "translate-x-0.5"
                      )}
                    />
                  </button>
                </div>
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Smartphone size={18} className="text-gray-400" />
                    <div>
                      <div className="text-white text-sm font-medium">Push</div>
                      <div className="text-xs text-gray-400">Send push notifications to your device</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsPushEnabled(!isPushEnabled)}
                    className={cn(
                      "w-10 h-5 rounded-full transition-colors",
                      isPushEnabled ? "bg-blue-500" : "bg-gray-600"
                    )}
                  >
                    <div
                      className={cn(
                        "w-4 h-4 bg-white rounded-full transition-transform",
                        isPushEnabled ? "translate-x-5" : "translate-x-0.5"
                      )}
                    />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )
      case 'personalization':
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Agent Instructions</h3>
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
                <div className="p-4">
                  <textarea
                    value={agentInstructions}
                    onChange={(e) => setAgentInstructions(e.target.value)}
                    placeholder="Tell Pulse how you’d like it to behave. Ex: Be concise, prefer bullet points, always confirm before deleting."
                    className="w-full bg-transparent text-white placeholder-gray-500 text-sm outline-none resize-y min-h-[100px]"
                  />
                  <div className="mt-2 text-xs text-gray-500">Saved to your profile. Applied across devices.</div>
                </div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Memories</h3>
                <span className="text-xs text-gray-500">{agentMemories.length}/500</span>
              </div>
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
                <div className="p-4">
                  <textarea
                    value={agentMemories}
                    onChange={(e) => setAgentMemories(e.target.value.slice(0,500))}
                    placeholder="Ex: I’m a CS student, part‑time barista, evenings are best for studying, prefer weekly planning on Sundays."
                    className="w-full bg-transparent text-white placeholder-gray-500 text-sm outline-none resize-y min-h-[140px]"
                    maxLength={500}
                  />
                  <p className="mt-2 text-xs text-gray-500">Context Pulse can reference when helping you (preferences, routines, constraints).</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={saveProfile}
                className={cn(components.button.base, components.button.primary)}
              >
                Save
              </button>
              <button
                onClick={savePersonalization}
                className={cn(components.button.base, components.button.secondary)}
              >
                Save Agent Personalization
              </button>
              {personalizationSavedAt && (
                <span className="text-xs text-gray-500">Saved {new Date(personalizationSavedAt).toLocaleTimeString()}</span>
              )}
            </div>
          </div>
        )
      case 'premium':
        const isPremium = profile?.subscription_status === 'premium'
        return (
          <div className="space-y-6">
            {/* Premium Header */}
            <div className={cnTokens(components.card.base, "border-2 border-blue-500/30")}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <Sparkles size={24} className="text-blue-400" />
                  </div>
                  <div>
                    <h3 className={cnTokens(typography.body.large, "font-semibold", colors.text.primary)}>
                      {isPremium ? 'PulsePlan Premium' : 'Upgrade'}
                    </h3>
                    {isPremium && (
                      <p className={cnTokens(typography.body.small, colors.text.secondary, "mt-0.5")}>
                        Your plan auto-renews on Nov 19, 2025
                      </p>
                    )}
                  </div>
                </div>
                <button 
                  onClick={() => navigate('/pricing')}
                  className={cnTokens(components.button.base, components.button.secondary)}
                >
                  {isPremium ? 'Manage' : 'Upgrade plan'}
                </button>
              </div>
              <div className={cnTokens(components.divider.horizontal, "my-4")}></div>
              {isPremium ? (
                <>
                  <p className={cnTokens(typography.body.default, colors.text.secondary)}>
                    Thanks for subscribing to PulsePlan Premium! Your Premium plan includes:
                  </p>
                  <div className={cnTokens(spacing.stack.md, "mt-4")}>
                    {[
                      'Basic task + deadline management',
                      'Unlimited schedules per week',
                      'Google/Apple Calendar integration',
                      'Unlimited agent access',
                      'Unlimited canvas sync (all courses)',
                      'Unlimited task storage',
                      'AI task breakdown & automation',
                      'Smart auto-scheduling & rescheduling',
                      'Long term memory of you',
                      'Auto-draft & summarize emails',
                      'Daily AI morning briefings',
                      'Custom AI preferences',
                      'Priority support & early access',
                    ].map((feature, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <Check size={18} className={cnTokens(colors.text.success, "mt-0.5 flex-shrink-0")} />
                        <p className={cnTokens(typography.body.default, colors.text.primary)}>{feature}</p>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <>
                  <p className={cnTokens(typography.body.default, colors.text.secondary)}>
                    Upgrade to PulsePlan Premium to unlock advanced features:
                  </p>
                  <div className={cnTokens(spacing.stack.md, "mt-4")}>
                    {[
                      { text: 'Basic task + deadline management', included: true },
                      { text: '1 schedule per week', included: true },
                      { text: 'Google/Apple Calendar integration', included: true },
                      { text: 'Limited agent access', included: true },
                      { text: 'Limited canvas sync (1 course)', included: true },
                      { text: 'Limited task storage', included: true },
                      { text: 'AI task breakdown & automation', included: false },
                      { text: 'Smart auto-scheduling & rescheduling', included: false },
                      { text: 'Unlimited Canvas sync (all courses)', included: false },
                      { text: 'Long term memory of you', included: false },
                      { text: 'Auto-draft & summarize emails', included: false },
                      { text: 'Daily AI morning briefings', included: false },
                      { text: 'Custom AI preferences', included: false },
                      { text: 'Priority support & early access', included: false },
                    ].map((feature, index) => (
                      <div key={index} className="flex items-start gap-3">
                        {feature.included ? (
                          <Check size={18} className={cnTokens(colors.text.success, "mt-0.5 flex-shrink-0")} />
                        ) : (
                          <X size={18} className={cnTokens(colors.text.muted, "mt-0.5 flex-shrink-0")} />
                        )}
                        <p className={cnTokens(
                          typography.body.default,
                          feature.included ? colors.text.primary : colors.text.muted
                        )}>
                          {feature.text}
                        </p>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        )
      case 'profile':
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Personal Information</h3>
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-gray-700/30">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <User size={14} className="text-gray-400" />
                      <p className="text-xs text-gray-400">Full Name</p>
                    </div>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Enter full name"
                      className={cn(components.input.base, "w-full")}
                    />
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Mail size={14} className="text-gray-400" />
                      <p className="text-xs text-gray-400">Email</p>
                    </div>
                    <input
                      type="email"
                      value={profile?.email || ''}
                      className={cn(components.input.base, "w-full opacity-50")}
                      disabled
                    />
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Academic Information</h3>
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-gray-700/30">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <School size={14} className="text-gray-400" />
                      <p className="text-xs text-gray-400">School</p>
                    </div>
                    <input
                      type="text"
                      value={school}
                      onChange={(e) => setSchool(e.target.value)}
                      placeholder="Enter school"
                      className={cn(components.input.base, "w-full")}
                    />
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Calendar size={14} className="text-gray-400" />
                      <p className="text-xs text-gray-400">Academic Year</p>
                    </div>
                    <input
                      type="text"
                      value={academicYear}
                      onChange={(e) => setAcademicYear(e.target.value)}
                      placeholder="Enter academic year"
                      className={cn(components.input.base, "w-full")}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex">
              <button
                onClick={saveProfile}
                disabled={updateProfileMutation.isPending || profileLoading}
                className={cn(
                  components.button.base,
                  components.button.primary,
                  "disabled:bg-gray-200 disabled:cursor-not-allowed"
                )}
              >
                {updateProfileMutation.isPending ? 'Saving...' : 'Save Profile'}
              </button>
            </div>
          </div>
        )

      case 'appearance':
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Choose a Theme</h3>
              <div className="space-y-2">
                {[
                  { id: 'dark', name: 'Dark', preview: 'bg-gray-800', selected: true },
                  { id: 'light', name: 'Light', preview: 'bg-white', selected: false },
                ].map((theme) => (
                  <div
                    key={theme.id}
                    className="flex items-center gap-3 p-3 rounded-lg transition-colors cursor-pointer bg-neutral-800/40 border border-gray-700/50 hover:bg-neutral-800/60"
                  >
                    <div className={cn("w-10 h-10 rounded-md", theme.preview)} />
                    <div className="flex-1 flex items-center gap-2">
                      <span className="text-white text-sm font-medium">{theme.name}</span>
                    </div>
                    <div className="w-5 h-5 rounded-full border-2 border-gray-500 flex items-center justify-center">
                      {theme.selected && <div className="w-2.5 h-2.5 bg-blue-500 rounded-full" />}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )

      case 'briefings':
        return (
          <div className="space-y-4">
            <p className="text-gray-400 text-sm">
              Customize your daily morning briefing to start each day informed and focused
            </p>

            <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b border-gray-700/30">
                <div className="flex items-center gap-2">
                  <Newspaper size={18} className="text-gray-400" />
                  <span className="text-sm text-white font-medium">Daily Briefings Enabled</span>
                </div>
                <button
                  onClick={() => setIsBriefingsEnabled(!isBriefingsEnabled)}
                  className={cn(
                    "w-10 h-5 rounded-full transition-colors",
                    isBriefingsEnabled ? "bg-blue-500" : "bg-gray-600"
                  )}
                >
                  <div className={cn(
                    "w-4 h-4 bg-white rounded-full transition-transform",
                    isBriefingsEnabled ? "translate-x-5" : "translate-x-0.5"
                  )} />
                </button>
              </div>

              <div className="flex items-center justify-between p-4 border-b border-gray-700/30">
                <div className="flex items-center gap-2">
                  <Clock size={18} className="text-gray-400" />
                  <span className="text-sm text-white font-medium">Delivery Time</span>
                </div>
                  <span className="text-xs text-gray-400">7:00 AM</span>
              </div>

              <div className="p-4">
                <button
                  onClick={handleSendTestBriefing}
                  disabled={testBriefingStatus === 'sending'}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors border",
                    testBriefingStatus === 'sending'
                      ? "bg-gray-600 text-gray-400 cursor-not-allowed border-gray-500"
                      : testBriefingStatus === 'success'
                      ? "bg-green-600 text-white border-green-500"
                      : testBriefingStatus === 'error'
                      ? "bg-red-600 text-white border-red-500"
                      : "bg-white text-black hover:bg-gray-100 border-gray-300"
                  )}
                >
                  <Mail size={14} />
                  {testBriefingStatus === 'sending' && (
                    <>
                      <RefreshCw size={14} className="animate-spin" />
                      Sending Test Briefing...
                    </>
                  )}
                  {testBriefingStatus === 'success' && 'Test Briefing Sent! Check Your Email'}
                  {testBriefingStatus === 'error' && 'Failed to Send - Try Again'}
                  {!testBriefingStatus && 'Send Test Briefing Now'}
                </button>
                <div className="flex items-center justify-center gap-1.5 text-xs text-gray-500 mt-2">
                  <Info size={12} className="text-gray-400" aria-hidden="true" />
                  <span>Get a preview of your daily briefing sent to your email right now</span>
                </div>
              </div>
            </div>

            {isBriefingsEnabled && (
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
                <div className="p-4 text-center border-b border-gray-700/50">
                  <h3 className="text-sm font-semibold text-white mb-0.5">Good Morning there</h3>
                  <p className="text-xs text-gray-400 italic">Here's your morning briefing</p>
                </div>
                
                <div className="p-4 space-y-3">
                  <div>
                    <h4 className={cn(typography.subsectionTitle, "mb-2")}>Schedule Overview</h4>
                    <textarea
                      value={scheduleContent}
                      onChange={(e) => setScheduleContent(e.target.value)}
                      className={cn(components.textarea.base, "w-full min-h-[50px]")}
                      placeholder="Describe what you want to see in your schedule overview..."
                    />
                  </div>

                  <div>
                    <h4 className={cn(typography.subsectionTitle, "mb-2")}>Suggested Adjustments</h4>
                    <textarea
                      value={suggestionsContent}
                      onChange={(e) => setSuggestionsContent(e.target.value)}
                      className={cn(components.textarea.base, "w-full min-h-[50px]")}
                      placeholder="Describe what AI suggestions you want to receive..."
                    />
                  </div>

                  <div>
                    <h4 className={cn(typography.subsectionTitle, "mb-2")}>Motivational Blurb</h4>
                    <textarea
                      value={motivationContent}
                      onChange={(e) => setMotivationContent(e.target.value)}
                      className={cn(components.textarea.base, "w-full min-h-[50px]")}
                      placeholder="Describe what kind of motivation you want to receive..."
                    />
                  </div>

                  <div>
                    <h4 className={cn(typography.subsectionTitle, "mb-2")}>Important Reminders</h4>
                    <textarea
                      value={remindersContent}
                      onChange={(e) => setRemindersContent(e.target.value)}
                      className={cn(components.textarea.base, "w-full min-h-[50px]")}
                      placeholder="Describe what reminders you want to see..."
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        )

      case 'courses':
        return (
          <div className="space-y-4">
            <p className="text-gray-400 text-sm mb-3">
              Manage your courses and customize their colors. These will be used to organize your assignments and schedule.
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
                    onClick={() => handleCoursePress(course)}
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

      case 'tags':
        const predefinedTags = tags.filter(t => t.type === 'predefined')
        const userTags = tags.filter(t => t.type === 'user')

        return (
          <div className="space-y-4">
            <p className="text-xs text-gray-400 mb-3">
              Pulse automatically applies predefined tags to your tasks. Add your own custom tags to organize tasks however you want.
            </p>

            {/* Create New Tag */}
            <div className="mb-3">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  placeholder="Create new tag..."
                  onKeyPress={(e) => e.key === 'Enter' && handleCreateTag()}
                  className={cn(components.input.base, "flex-1")}
                />
                <button
                  onClick={handleCreateTag}
                  disabled={!newTagName.trim() || isCreatingTag}
                  className={cn(
                    components.button.base,
                    components.button.primary,
                    "flex items-center gap-1 disabled:bg-gray-200 disabled:cursor-not-allowed"
                  )}
                >
                  <Plus size={12} />
                  Add
                </button>
              </div>
            </div>

            {/* User Tags */}
            {userTags.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Your Tags</h4>
                <div className="flex flex-wrap gap-2">
                  {userTags.map((tag) => (
                    <div
                      key={`${tag.name}-${tag.id || 'no-id'}`}
                      className="bg-neutral-800/40 rounded-lg px-2 py-1 flex items-center gap-1.5"
                    >
                      <span className="text-xs text-white">{tag.name}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteTag(tag)
                        }}
                        className="text-gray-500 hover:text-red-400 transition-colors"
                        title="Delete tag"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Predefined Tags */}
            <div>
              <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Predefined Tags</h4>
              {predefinedTags.length === 0 ? (
                <p className="text-gray-500 text-sm">No predefined tags available.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {predefinedTags.map((tag) => (
                    <div
                      key={tag.name}
                      className="bg-neutral-800/40 rounded-lg px-2 py-1 flex items-center gap-1.5"
                    >
                      <span className="text-xs text-white">{tag.name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {tagsLoading && (
              <div className="flex items-center justify-center py-12">
                <p className="text-gray-400">Loading tags...</p>
              </div>
            )}
          </div>
        )

      case 'hobbies':
        return (
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-sm">Add your hobbies and interests. PulsePlan will intelligently make time for them.</p>
            </div>
            <div className="flex items-center justify-end">
              <button
                onClick={handleAddHobby}
                className={cn(components.button.base, components.button.primary, "flex items-center gap-1")}
              >
                <Plus size={12} />
                Add Hobby
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {hobbies.map((hobby) => (
                <div key={hobby.id} className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4 flex items-start gap-3">
                  <div className="shrink-0 mt-0.5">{getHobbyIcon(hobby.icon)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="text-white text-sm font-medium truncate">{hobby.name || 'Untitled'}</h4>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleEditHobby(hobby)}
                          className="p-1.5 text-gray-400 hover:text-white hover:bg-neutral-700/40 rounded transition-colors"
                          title="Edit hobby"
                        >
                          <Pen size={14} />
                        </button>
                        <button
                          onClick={() => handleDeleteHobby(hobby.id)}
                          className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                          title="Delete hobby"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-1 line-clamp-2">{hobby.notes}</p>
                    <div className="mt-2 text-xs text-gray-500">
                      {hobby.preferred_time} • {hobby.duration_min === hobby.duration_max ? `${hobby.duration_min} min` : `${hobby.duration_min}-${hobby.duration_max} min`}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {showHobbyModal && selectedHobby && (
              <div className={components.modal.overlay}>
                <div className={cn(components.modal.container, "max-w-md")}>
                  <div className={components.modal.header}>
                    <div className="flex items-center justify-between w-full">
                      <h3 className={components.modal.title}>{selectedHobby.name ? 'Edit Hobby' : 'Add Hobby'}</h3>
                      <button onClick={() => { setShowHobbyModal(false); setSelectedHobby(null) }} className="text-gray-400 hover:text-white transition-colors">
                        <X size={18} />
                      </button>
                    </div>
                  </div>
                  <div className={cn(components.modal.content, spacing.stack.md)}>
                    <div>
                      <label className={components.input.label}>Name</label>
                      <input className={cn(components.input.base, "w-full")} value={selectedHobby.name} onChange={(e) => setSelectedHobby({ ...selectedHobby, name: e.target.value })} />
                    </div>
                    <div>
                      <label className={components.input.label}>Notes</label>
                      <textarea className={cn(components.textarea.base, "w-full min-h-[80px]")} value={selectedHobby.notes || ''} onChange={(e) => setSelectedHobby({ ...selectedHobby, notes: e.target.value })} />
                    </div>
                    <div>
                      <label className={components.input.label}>Preferred Time</label>
                      <select className={cn(components.select.base, "w-full")} value={selectedHobby.preferred_time} onChange={(e) => setSelectedHobby({ ...selectedHobby, preferred_time: e.target.value as any })}>
                        <option value="morning">Morning</option>
                        <option value="afternoon">Afternoon</option>
                        <option value="evening">Evening</option>
                        <option value="night">Night</option>
                        <option value="any">Anytime</option>
                      </select>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className={components.input.label}>Min Duration (min)</label>
                        <input type="number" min={5} step={5} className={cn(components.input.base, "w-full")} value={selectedHobby.duration_min || 30} onChange={(e) => setSelectedHobby({ ...selectedHobby, duration_min: Number(e.target.value) })} />
                      </div>
                      <div>
                        <label className={components.input.label}>Max Duration (min)</label>
                        <input type="number" min={5} step={5} className={cn(components.input.base, "w-full")} value={selectedHobby.duration_max || 60} onChange={(e) => setSelectedHobby({ ...selectedHobby, duration_max: Number(e.target.value) })} />
                      </div>
                    </div>
                    <div>
                      <label className={components.input.label}>Flexibility</label>
                      <select className={cn(components.select.base, "w-full")} value={selectedHobby.flexibility} onChange={(e) => setSelectedHobby({ ...selectedHobby, flexibility: e.target.value as any })}>
                        <option value="low">Low (strict timing)</option>
                        <option value="medium">Medium (somewhat flexible)</option>
                        <option value="high">High (very flexible)</option>
                      </select>
                    </div>
                    <div>
                      <label className={components.input.label}>Icon</label>
                      <div className="mt-1 grid grid-cols-7 gap-1.5">
                        {(['Music','Camera','Book','Gamepad2','Palette','Dumbbell','Bike','Coffee','Film','Heart','Users','Target','Mountain','MountainSnow'] as any[]).map((i) => (
                          <button key={i} onClick={() => setSelectedHobby({ ...selectedHobby, icon: i })} className={cn('p-1 rounded border transition-colors aspect-square flex items-center justify-center', selectedHobby.icon === i ? 'border-white/70 bg-white/10' : 'border-gray-700/50 hover:bg-neutral-800/40')}>{getHobbyIcon(i)}</button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className={components.modal.footer}>
                    <button onClick={() => { setShowHobbyModal(false); setSelectedHobby(null) }} className={cn(components.button.base, components.button.secondary)}>Cancel</button>
                    <button onClick={handleSaveHobby} className={cn(components.button.base, components.button.primary)}>Save</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )

      case 'weekly-pulse':
        const getDayDisplayValue = () => {
          const time = '6:00 AM'
          switch (weeklyPulseDay) {
            case 'sunday': return `Sunday, ${time}`
            case 'monday': return `Monday, ${time}`
            case 'friday': return `Friday, ${time}`
          }
        }

        return (
          <div className="space-y-4">
            <p className="text-gray-400 text-sm">
              Customize your weekly recap email by defining what you want to receive in each section
            </p>

            {/* General Settings */}
            <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
              <div className="p-4 flex items-center justify-between border-b border-gray-700/30">
                <div className="flex items-center gap-3">
                  <Mail size={18} className="text-gray-400" />
                  <div>
                    <div className="text-white text-sm font-medium">Weekly Pulse Enabled</div>
                  </div>
                </div>
                <button
                  onClick={() => setIsWeeklyPulseEnabled(!isWeeklyPulseEnabled)}
                  className={cn(
                    "w-10 h-5 rounded-full transition-colors",
                    isWeeklyPulseEnabled ? "bg-blue-500" : "bg-gray-600"
                  )}
                >
                  <div
                    className={cn(
                      "w-4 h-4 bg-white rounded-full transition-transform",
                      isWeeklyPulseEnabled ? "translate-x-5" : "translate-x-0.5"
                    )}
                  />
                </button>
              </div>

              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Calendar size={18} className="text-gray-400" />
                  <div>
                    <div className="text-white text-sm font-medium">Delivery Schedule</div>
                  </div>
                </div>
                <button
                  onClick={() => setShowDaySelection(!showDaySelection)}
                  className="text-xs text-gray-400 hover:text-white transition-colors"
                  disabled={!isWeeklyPulseEnabled}
                >
                  {isWeeklyPulseEnabled ? getDayDisplayValue() : 'None'}
                </button>
              </div>
            </div>

            {/* Day Selection */}
            {showDaySelection && isWeeklyPulseEnabled && (
              <div className="space-y-2">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Delivery Day</h3>
                <div className="flex gap-2">
                  {(['sunday', 'monday', 'friday'] as const).map((day) => (
                    <button
                      key={day}
                      onClick={() => setWeeklyPulseDay(day)}
                      className={cn(
                        "flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors border",
                        weeklyPulseDay === day
                          ? "bg-blue-500 text-white border-blue-500"
                          : "bg-neutral-800/40 text-white border-gray-700/50 hover:bg-neutral-800/60"
                      )}
                    >
                      {day.charAt(0).toUpperCase() + day.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {isWeeklyPulseEnabled && (
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
                <div className="p-4 text-center border-b border-gray-700/50">
                  <h3 className="text-sm font-semibold text-white mb-0.5">The Weekly Pulse</h3>
                  <p className="text-xs text-gray-400 italic">Your Personalized Academic Digest</p>
                </div>

                <div className="p-4 space-y-3">
                  <div>
                    <h4 className={cn(typography.subsectionTitle, "mb-2")}>Upcoming Tasks</h4>
                    <textarea
                      value={upcomingTasksContent}
                      onChange={(e) => setUpcomingTasksContent(e.target.value)}
                      className={cn(components.textarea.base, "w-full min-h-[50px]")}
                      placeholder="Describe what you want to see for upcoming tasks..."
                    />
                  </div>

                  <div>
                    <h4 className={cn(typography.subsectionTitle, "mb-2")}>Overdue Items</h4>
                    <textarea
                      value={overdueItemsContent}
                      onChange={(e) => setOverdueItemsContent(e.target.value)}
                      className={cn(components.textarea.base, "w-full min-h-[50px]")}
                      placeholder="Describe what you want to see for overdue items..."
                    />
                  </div>

                  <div>
                    <h4 className={cn(typography.subsectionTitle, "mb-2")}>Study Habits Summary</h4>
                    <textarea
                      value={studyHabitsContent}
                      onChange={(e) => setStudyHabitsContent(e.target.value)}
                      className={cn(components.textarea.base, "w-full min-h-[50px]")}
                      placeholder="Describe what insights you want about your study habits..."
                    />
                  </div>

                  <div>
                    <h4 className={cn(typography.subsectionTitle, "mb-2")}>Personal Streaks & Milestones</h4>
                    <textarea
                      value={streaksContent}
                      onChange={(e) => setStreaksContent(e.target.value)}
                      className={cn(components.textarea.base, "w-full min-h-[50px]")}
                      placeholder="Describe what achievements and progress you want to see..."
                    />
                  </div>

                  <div>
                    <h4 className={cn(typography.subsectionTitle, "mb-2")}>Optional Content</h4>
                    <textarea
                      value={optionalPulseContent}
                      onChange={(e) => setOptionalPulseContent(e.target.value)}
                      className={cn(components.textarea.base, "w-full min-h-[50px]")}
                      placeholder="Add any additional content you'd like to receive (leave blank if not needed)..."
                    />
                  </div>
                </div>
              </div>
            )}

            <div className="bg-neutral-800/40 border border-gray-700/50 rounded-lg p-4">
              <p className="text-xs text-gray-400 text-center leading-relaxed">
                {isWeeklyPulseEnabled
                  ? `Your Weekly Pulse will be delivered every ${weeklyPulseDay.charAt(0).toUpperCase() + weeklyPulseDay.slice(1)} at 6:00 AM. Customize each section above to receive exactly the insights you need.`
                  : 'Enable Weekly Pulse to receive personalized weekly insights, productivity analytics, upcoming task summaries, and progress tracking delivered directly to your email.'}
              </p>
            </div>
          </div>
        )

      case 'study':
        const formatTime = (hour: number) => {
          const period = hour >= 12 ? 'PM' : 'AM'
          const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
          return `${displayHour}:00 ${period}`
        }

        return (
          <div className="space-y-4">
            <p className="text-gray-400 text-sm">
              Set your preferred study hours. PulsePlan will schedule tasks and send reminders during these times.
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-3">
                  <Sun size={24} className="text-blue-500" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-400 mb-1">Start Time</p>
                    <p className="text-lg font-semibold text-white">{formatTime(studyStartHour)}</p>
                  </div>
                </div>
                <input
                  type="range"
                  min="0"
                  max="23"
                  value={studyStartHour}
                  onChange={(e) => setStudyStartHour(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                  style={{
                    accentColor: '#3b82f6'
                  }}
                />
              </div>

              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-3">
                  <Moon size={24} className="text-blue-500" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-400 mb-1">End Time</p>
                    <p className="text-lg font-semibold text-white">{formatTime(studyEndHour)}</p>
                  </div>
                </div>
                <input
                  type="range"
                  min="0"
                  max="23"
                  value={studyEndHour}
                  onChange={(e) => setStudyEndHour(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                  style={{
                    accentColor: '#3b82f6'
                  }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Daily Schedule</h3>
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4">
                <div className="flex justify-between text-xs text-gray-400 mb-2">
                  <span>12 AM</span>
                  <span>12 PM</span>
                  <span>11 PM</span>
                </div>
                <div className="flex h-6 bg-neutral-900 rounded-lg overflow-hidden">
                  {Array.from({ length: 24 }).map((_, hour) => {
                    const isInRange =
                      studyStartHour <= studyEndHour
                        ? hour >= studyStartHour && hour <= studyEndHour
                        : hour >= studyStartHour || hour <= studyEndHour
                    return (
                      <div
                        key={hour}
                        className={cn(
                          'flex-1 border-r border-gray-800/50',
                          isInRange ? 'bg-blue-500' : 'bg-transparent'
                        )}
                      />
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">{navigationItems.find(item => item.id === activeSection)?.label}</h3>
              <p className="text-gray-400">Settings for {navigationItems.find(item => item.id === activeSection)?.label.toLowerCase()} coming soon.</p>
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
                    onClick={activeSection === 'courses' ? fetchCourses : fetchTags}
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
          onClose={() => setShowColorPicker(false)}
          onSelectColor={handleColorSelect}
          currentColor={selectedCourse?.color || '#6366F1'}
          courseName={selectedCourse?.canvas_course_code || selectedCourse?.name || ''}
        />
          </>
        ) : null}

      {/* New Conversational Hobby Modals */}
      <AddHobbyPrompt
        isOpen={showAddHobbyPrompt}
        onClose={() => setShowAddHobbyPrompt(false)}
        onSubmit={handleHobbyDescriptionSubmit}
        isLoading={isParsingHobby}
      />

      <HobbySummary
        isOpen={showHobbySummary}
        hobby={parsedHobby}
        confidence={hobbyConfidence}
        onClose={() => {
          setShowHobbySummary(false)
          setParsedHobby(null)
        }}
        onConfirm={handleHobbyConfirm}
        onEdit={handleHobbyEdit}
      />
      </div>
    </div>
  )
}