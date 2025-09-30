import React, { useState } from 'react'
import { 
  X, 
  User, 
  Settings, 
  Bell, 
  Calendar, 
  Database, 
  Cloud, 
  Link, 
  HelpCircle,
  ExternalLink,
  ChevronDown,
  ChevronLeft,
  Mail,
  School,
  Clock,
  Star,
  Lock
} from 'lucide-react'
import { Button } from './ui/button'
import { cn } from '../lib/utils'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

type SettingsSection = 'profile' | 'appearance' | 'briefings' | 'hobbies' | 'reminders' | 'study' | 'subjects' | 'weekly-pulse'

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeSection, setActiveSection] = useState<SettingsSection>('profile')
  const [fullName, setFullName] = useState('')
  const [school, setSchool] = useState('')
  const [academicYear, setAcademicYear] = useState('')
  const [email, setEmail] = useState('user@example.com')
  
  // Briefings settings
  const [isBriefingsEnabled, setIsBriefingsEnabled] = useState(true)
  const [deliveryTime, setDeliveryTime] = useState('7:00 AM')
  const [scheduleContent, setScheduleContent] = useState('Show me today\'s schedule with time blocks, priorities, and any potential conflicts or gaps.')
  const [suggestionsContent, setSuggestionsContent] = useState('Provide AI-powered recommendations for optimizing my day, including schedule adjustments and productivity tips.')
  const [motivationContent, setMotivationContent] = useState('Include a brief motivational message or academic tip to start my day with focus and energy.')
  const [remindersContent, setRemindersContent] = useState('Highlight important deadlines, upcoming assignments, and tasks that need my attention today.')

  if (!isOpen) return null

  const navigationItems = [
    { id: 'profile' as SettingsSection, label: 'Profile', icon: User },
    { id: 'appearance' as SettingsSection, label: 'Appearance', icon: Settings },
    { id: 'briefings' as SettingsSection, label: 'Briefings', icon: Bell },
    { id: 'hobbies' as SettingsSection, label: 'Hobbies', icon: Star },
    { id: 'reminders' as SettingsSection, label: 'Reminders', icon: Clock },
    { id: 'study' as SettingsSection, label: 'Study', icon: School },
    { id: 'subjects' as SettingsSection, label: 'Subjects', icon: Database },
    { id: 'weekly-pulse' as SettingsSection, label: 'Weekly Pulse', icon: Calendar },
  ]

  const renderSettingsContent = () => {
    switch (activeSection) {
      case 'profile':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">Personal Information</h3>
              <div className="bg-neutral-800 rounded-xl overflow-hidden">
                <div className="flex items-center gap-4 p-4 border-b border-gray-700">
                  <User size={20} className="text-gray-400" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-400 mb-1">Full Name</p>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Enter full name"
                      className="w-full bg-transparent text-white text-base focus:outline-none"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-4 p-4">
                  <Mail size={20} className="text-gray-400" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-400 mb-1">Email</p>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-transparent text-white text-base focus:outline-none opacity-50"
                      disabled
                    />
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">Academic Information</h3>
              <div className="bg-neutral-800 rounded-xl overflow-hidden">
                <div className="flex items-center gap-4 p-4 border-b border-gray-700">
                  <School size={20} className="text-gray-400" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-400 mb-1">School</p>
                    <input
                      type="text"
                      value={school}
                      onChange={(e) => setSchool(e.target.value)}
                      placeholder="Enter school"
                      className="w-full bg-transparent text-white text-base focus:outline-none"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-4 p-4">
                  <Calendar size={20} className="text-gray-400" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-400 mb-1">Academic Year</p>
                    <input
                      type="text"
                      value={academicYear}
                      onChange={(e) => setAcademicYear(e.target.value)}
                      placeholder="Enter academic year"
                      className="w-full bg-transparent text-white text-base focus:outline-none"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )

      case 'appearance':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">Choose a Theme</h3>
              <div className="space-y-3">
                {[
                  { id: 'dark', name: 'Dark', preview: 'bg-gray-800', selected: true },
                  { id: 'light', name: 'Light', preview: 'bg-white', premium: true },
                  { id: 'dark-agent', name: 'Dark Agent', preview: 'bg-gray-900', premium: true },
                ].map((theme) => (
                  <div
                    key={theme.id}
                    className="flex items-center gap-4 p-4 bg-neutral-800 rounded-xl hover:bg-neutral-750 transition-colors cursor-pointer"
                  >
                    <div className={cn("w-12 h-12 rounded-lg", theme.preview)} />
                    <div className="flex-1 flex items-center gap-2">
                      <span className="text-white font-medium">{theme.name}</span>
                      {theme.premium && (
                        <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                          <Star size={12} className="text-white fill-white" />
                        </div>
                      )}
                    </div>
                    <div className="w-6 h-6 rounded-full border-2 border-gray-500 flex items-center justify-center">
                      {theme.selected && <div className="w-3 h-3 bg-blue-500 rounded-full" />}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )

      case 'briefings':
        return (
          <div className="space-y-6">
            <p className="text-gray-400 text-center text-sm leading-5">
              Customize your daily morning briefing to start each day informed and focused
            </p>

            <div className="bg-neutral-800 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <div className="flex items-center gap-3">
                  <Bell size={20} className="text-gray-400" />
                  <span className="text-white font-medium">Daily Briefings Enabled</span>
                </div>
                <button
                  onClick={() => setIsBriefingsEnabled(!isBriefingsEnabled)}
                  className={cn(
                    "w-12 h-6 rounded-full transition-colors",
                    isBriefingsEnabled ? "bg-blue-500" : "bg-gray-600"
                  )}
                >
                  <div className={cn(
                    "w-5 h-5 bg-white rounded-full transition-transform",
                    isBriefingsEnabled ? "translate-x-6" : "translate-x-0.5"
                  )} />
                </button>
              </div>
              
              <div className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <Clock size={20} className="text-gray-400" />
                  <span className="text-white font-medium">Delivery Time</span>
                </div>
                <span className="text-gray-400">{isBriefingsEnabled ? deliveryTime : 'None'}</span>
              </div>
            </div>

            {isBriefingsEnabled && (
              <div className="bg-neutral-800 rounded-2xl overflow-hidden">
                <div className="p-5 text-center border-b-2 border-black">
                  <h3 className="text-2xl font-bold text-white mb-1">Good Morning there</h3>
                  <p className="text-gray-400 italic">Here's your morning briefing</p>
                </div>
                
                <div className="p-5 space-y-4">
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Schedule Overview</h4>
                    <textarea
                      value={scheduleContent}
                      onChange={(e) => setScheduleContent(e.target.value)}
                      className="w-full p-3 bg-neutral-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none min-h-[60px]"
                      placeholder="Describe what you want to see in your schedule overview..."
                    />
                  </div>
                  
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Suggested Adjustments</h4>
                    <textarea
                      value={suggestionsContent}
                      onChange={(e) => setSuggestionsContent(e.target.value)}
                      className="w-full p-3 bg-neutral-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none min-h-[60px]"
                      placeholder="Describe what AI suggestions you want to receive..."
                    />
                  </div>
                  
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Motivational Blurb</h4>
                    <textarea
                      value={motivationContent}
                      onChange={(e) => setMotivationContent(e.target.value)}
                      className="w-full p-3 bg-neutral-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none min-h-[60px]"
                      placeholder="Describe what kind of motivation you want to receive..."
                    />
                  </div>
                  
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Important Reminders</h4>
                    <textarea
                      value={remindersContent}
                      onChange={(e) => setRemindersContent(e.target.value)}
                      className="w-full p-3 bg-neutral-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none min-h-[60px]"
                      placeholder="Describe what reminders you want to see..."
                    />
                  </div>
                </div>
              </div>
            )}
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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-neutral-900 rounded-2xl w-full max-w-4xl h-[70vh] flex overflow-hidden shadow-2xl">
        {/* Left Sidebar */}
        <div className="w-56 bg-neutral-800 flex flex-col">
          {/* Logo */}
          <div className="px-5 py-5">
            <div className="flex items-center gap-3">
              <img 
                src="/pulse.png" 
                alt="PulsePlan" 
                className="w-8 h-8 rounded-lg"
              />
              <span className="text-white font-semibold text-lg">PulsePlan</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-3 space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon
              const isActive = activeSection === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-colors",
                    isActive 
                      ? "bg-neutral-700 text-white" 
                      : "text-gray-400 hover:text-white hover:bg-neutral-700/50"
                  )}
                >
                  <Icon size={18} />
                  <span className="text-sm font-medium">{item.label}</span>
                </button>
              )
            })}
          </nav>

          {/* Help Link */}
          <div className="px-3 py-3 border-t border-gray-700">
            <a
              href="#"
              className="flex items-center gap-3 text-gray-400 hover:text-white transition-colors"
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
          <div className="px-5 py-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">
                {navigationItems.find(item => item.id === activeSection)?.label || 'Settings'}
              </h2>
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-neutral-800"
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 px-5 py-5 overflow-y-auto">
            {renderSettingsContent()}
          </div>
        </div>
      </div>
    </div>
  )
}
