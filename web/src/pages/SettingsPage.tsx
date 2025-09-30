import React, { useState } from 'react'
import { 
  User, 
  Bell, 
  Palette, 
  Shield, 
  HelpCircle, 
  LogOut,
  Settings as SettingsIcon,
  Smartphone,
  Monitor,
  Sun,
  Moon,
  Globe,
  Trash2,
  Download
} from 'lucide-react'
import { ProfileSettings } from '../features/settings/ProfileSettings'
import { signOut } from '../lib/supabase'

type SettingsTab = 'profile' | 'notifications' | 'appearance' | 'privacy' | 'help'

const tabs = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'privacy', label: 'Privacy & Security', icon: Shield },
  { id: 'help', label: 'Help & Support', icon: HelpCircle },
] as const

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile')

  const handleSignOut = async () => {
    if (window.confirm('Are you sure you want to sign out?')) {
      await signOut()
      window.location.reload()
    }
  }

  const handleDeleteAccount = () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      // In a real app, this would call a delete account API
      console.log('Delete account requested')
    }
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return <ProfileSettings />
      
      case 'notifications':
        return (
          <div className="max-w-2xl">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-textPrimary mb-2">Notification Settings</h2>
              <p className="text-textSecondary">
                Choose when and how you want to receive notifications
              </p>
            </div>

            <div className="space-y-6">
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Task Reminders</h3>
                <div className="space-y-4">
                  <label className="flex items-center justify-between">
                    <div>
                      <div className="text-textPrimary font-medium">Due Date Reminders</div>
                      <div className="text-sm text-textSecondary">Get notified when tasks are due</div>
                    </div>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </label>
                  <label className="flex items-center justify-between">
                    <div>
                      <div className="text-textPrimary font-medium">Daily Summary</div>
                      <div className="text-sm text-textSecondary">Daily overview of your tasks</div>
                    </div>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </label>
                  <label className="flex items-center justify-between">
                    <div>
                      <div className="text-textPrimary font-medium">Weekly Review</div>
                      <div className="text-sm text-textSecondary">Weekly productivity insights</div>
                    </div>
                    <input type="checkbox" className="rounded" />
                  </label>
                </div>
              </div>

              <div className="card p-6">
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Agent Notifications</h3>
                <div className="space-y-4">
                  <label className="flex items-center justify-between">
                    <div>
                      <div className="text-textPrimary font-medium">AI Suggestions</div>
                      <div className="text-sm text-textSecondary">Productivity tips and suggestions</div>
                    </div>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </label>
                  <label className="flex items-center justify-between">
                    <div>
                      <div className="text-textPrimary font-medium">Schedule Conflicts</div>
                      <div className="text-sm text-textSecondary">Alert when tasks overlap</div>
                    </div>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </label>
                </div>
              </div>
            </div>
          </div>
        )

      case 'appearance':
        return (
          <div className="max-w-2xl">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-textPrimary mb-2">Appearance</h2>
              <p className="text-textSecondary">
                Customize how PulsePlan looks and feels
              </p>
            </div>

            <div className="space-y-6">
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Theme</h3>
                <div className="grid grid-cols-3 gap-4">
                  <label className="flex flex-col items-center p-4 border border-primary rounded-lg cursor-pointer">
                    <input type="radio" name="theme" value="dark" defaultChecked className="sr-only" />
                    <Moon className="w-6 h-6 text-primary mb-2" />
                    <span className="text-sm text-textPrimary font-medium">Dark</span>
                    <span className="text-xs text-textSecondary">Current</span>
                  </label>
                  <label className="flex flex-col items-center p-4 border border-gray-600 rounded-lg cursor-pointer hover:border-gray-500">
                    <input type="radio" name="theme" value="light" className="sr-only" />
                    <Sun className="w-6 h-6 text-textSecondary mb-2" />
                    <span className="text-sm text-textPrimary font-medium">Light</span>
                    <span className="text-xs text-textSecondary">Coming soon</span>
                  </label>
                  <label className="flex flex-col items-center p-4 border border-gray-600 rounded-lg cursor-pointer hover:border-gray-500">
                    <input type="radio" name="theme" value="auto" className="sr-only" />
                    <Monitor className="w-6 h-6 text-textSecondary mb-2" />
                    <span className="text-sm text-textPrimary font-medium">Auto</span>
                    <span className="text-xs text-textSecondary">Coming soon</span>
                  </label>
                </div>
              </div>

              <div className="card p-6">
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Display</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-2">
                      Calendar View
                    </label>
                    <select className="input w-full">
                      <option value="week">Week View (Default)</option>
                      <option value="month">Month View</option>
                      <option value="day">Day View</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-2">
                      Date Format
                    </label>
                    <select className="input w-full">
                      <option value="US">MM/DD/YYYY (US)</option>
                      <option value="EU">DD/MM/YYYY (EU)</option>
                      <option value="ISO">YYYY-MM-DD (ISO)</option>
                    </select>
                  </div>
                  <label className="flex items-center justify-between">
                    <div>
                      <div className="text-textPrimary font-medium">24-Hour Time</div>
                      <div className="text-sm text-textSecondary">Use 24-hour time format</div>
                    </div>
                    <input type="checkbox" className="rounded" />
                  </label>
                </div>
              </div>
            </div>
          </div>
        )

      case 'privacy':
        return (
          <div className="max-w-2xl">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-textPrimary mb-2">Privacy & Security</h2>
              <p className="text-textSecondary">
                Manage your privacy settings and account security
              </p>
            </div>

            <div className="space-y-6">
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Account Security</h3>
                <div className="space-y-4">
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="text-textPrimary font-medium">Change Password</div>
                    <div className="text-sm text-textSecondary">Update your account password</div>
                  </button>
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="text-textPrimary font-medium">Two-Factor Authentication</div>
                    <div className="text-sm text-textSecondary">Add extra security to your account</div>
                  </button>
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="text-textPrimary font-medium">Active Sessions</div>
                    <div className="text-sm text-textSecondary">See where you're logged in</div>
                  </button>
                </div>
              </div>

              <div className="card p-6">
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Data & Privacy</h3>
                <div className="space-y-4">
                  <label className="flex items-center justify-between">
                    <div>
                      <div className="text-textPrimary font-medium">Analytics</div>
                      <div className="text-sm text-textSecondary">Help improve the app with usage data</div>
                    </div>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </label>
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="flex items-center gap-2">
                      <Download className="w-4 h-4 text-primary" />
                      <div>
                        <div className="text-textPrimary font-medium">Export Data</div>
                        <div className="text-sm text-textSecondary">Download all your data</div>
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              <div className="card p-6 border-error/20">
                <h3 className="text-lg font-semibold text-error mb-4">Danger Zone</h3>
                <button 
                  onClick={handleDeleteAccount}
                  className="w-full text-left p-3 bg-error/10 hover:bg-error/20 border border-error/20 rounded-lg transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Trash2 className="w-4 h-4 text-error" />
                    <div>
                      <div className="text-error font-medium">Delete Account</div>
                      <div className="text-sm text-error/80">Permanently delete your account and all data</div>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        )

      case 'help':
        return (
          <div className="max-w-2xl">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-textPrimary mb-2">Help & Support</h2>
              <p className="text-textSecondary">
                Get help and learn more about PulsePlan
              </p>
            </div>

            <div className="space-y-6">
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Resources</h3>
                <div className="space-y-4">
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="text-textPrimary font-medium">User Guide</div>
                    <div className="text-sm text-textSecondary">Learn how to use PulsePlan effectively</div>
                  </button>
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="text-textPrimary font-medium">Keyboard Shortcuts</div>
                    <div className="text-sm text-textSecondary">Speed up your workflow</div>
                  </button>
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="text-textPrimary font-medium">Video Tutorials</div>
                    <div className="text-sm text-textSecondary">Watch how-to videos</div>
                  </button>
                </div>
              </div>

              <div className="card p-6">
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Support</h3>
                <div className="space-y-4">
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="text-textPrimary font-medium">Contact Support</div>
                    <div className="text-sm text-textSecondary">Get help from our team</div>
                  </button>
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="text-textPrimary font-medium">Report a Bug</div>
                    <div className="text-sm text-textSecondary">Help us improve the app</div>
                  </button>
                  <button className="w-full text-left p-3 bg-surface hover:bg-gray-600 rounded-lg transition-colors">
                    <div className="text-textPrimary font-medium">Feature Request</div>
                    <div className="text-sm text-textSecondary">Suggest new features</div>
                  </button>
                </div>
              </div>

              <div className="card p-6">
                <h3 className="text-lg font-semibold text-textPrimary mb-4">About</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-textSecondary">Version</span>
                    <span className="text-textPrimary">1.0.0</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-textSecondary">Build</span>
                    <span className="text-textPrimary">2024.1.1</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-textSecondary">Platform</span>
                    <span className="text-textPrimary">Web</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="h-full flex">
      {/* Sidebar */}
      <div className="w-80 border-r border-gray-700 overflow-y-auto">
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-2xl font-bold text-textPrimary flex items-center gap-3">
            <SettingsIcon className="w-6 h-6" />
            Settings
          </h1>
        </div>
        
        <nav className="p-4">
          <div className="space-y-2">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors flex items-center gap-3 ${
                    activeTab === tab.id
                      ? 'bg-primary/20 text-primary'
                      : 'text-textSecondary hover:text-textPrimary hover:bg-surface'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {tab.label}
                </button>
              )
            })}
          </div>
          
          <div className="mt-8 pt-4 border-t border-gray-700">
            <button
              onClick={handleSignOut}
              className="w-full text-left p-3 rounded-lg transition-colors flex items-center gap-3 text-error hover:bg-error/10"
            >
              <LogOut className="w-5 h-5" />
              Sign Out
            </button>
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          {renderTabContent()}
        </div>
      </div>
    </div>
  )
}