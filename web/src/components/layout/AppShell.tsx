import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Home, 
  CalendarDays, 
  Settings, 
  HelpCircle,
  MessageSquarePlus,
  ListTodo,
  Grid3X3
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { ErrorBoundary } from '../ui/ErrorBoundary'
import { SettingsModal } from '../SettingsModal'
import { useAuthWebSocket } from '../../hooks/useAuthWebSocket'

interface AppShellProps {
  children: React.ReactNode
}

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Calendar', href: '/calendar', icon: CalendarDays },
  { name: 'Todos', href: '/todos', icon: ListTodo },
  { name: 'Integrations', href: '/integrations', icon: Grid3X3 },
]

export function AppShell({ children }: AppShellProps) {
  const location = useLocation()
  const [isCollapsed, setIsCollapsed] = useState(true)
  const [showSettings, setShowSettings] = useState(false)
  
  // Initialize WebSocket connection with user authentication
  useAuthWebSocket()


  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      {/* Sidebar */}
      <div className={`hidden md:flex md:flex-col transition-[width] duration-300 ease-in-out ${isCollapsed ? 'md:w-16' : 'md:w-56'} h-screen fixed left-0 top-0 z-10`}>
        <div className="flex flex-col h-full bg-neutral-800 overflow-x-hidden">
          {/* Logo */}
          <div className="px-5 py-5">
            <div className="flex items-center">
              <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors flex-shrink-0"
              >
                <img 
                  src="/pulse.png" 
                  alt="PulsePlan" 
                  className="w-8 h-8 rounded-lg"
                />
              </button>
              <span className={cn(
                "text-white font-semibold text-lg whitespace-nowrap transition-opacity duration-200 ml-3",
                isCollapsed ? "opacity-0" : "opacity-100"
              )}>
                PulsePlan
              </span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-3 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    "w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors",
                    isActive 
                      ? "bg-neutral-700 text-white" 
                      : "text-gray-400 hover:text-white hover:bg-neutral-700/50"
                  )}
                >
                  <item.icon size={18} className="flex-shrink-0" />
                  <span className={cn(
                    "text-sm font-medium whitespace-nowrap transition-opacity duration-200 ml-3",
                    isCollapsed ? "opacity-0" : "opacity-100"
                  )}>
                    {item.name}
                  </span>
                </Link>
              )
            })}
          </nav>

          {/* Divider */}
          <div className="mx-3 border-t border-gray-700/50"></div>

          {/* Bottom utility buttons */}
          <div className="px-3 py-3">
            <div className="space-y-1">
              {/* Settings button */}
              <button
                onClick={() => setShowSettings(true)}
                className={cn(
                  "w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors",
                  "text-gray-400 hover:text-white hover:bg-neutral-700/50"
                )}
              >
                <Settings size={18} className="flex-shrink-0" />
                <span className={cn(
                  "text-sm font-medium whitespace-nowrap transition-opacity duration-200 ml-3",
                  isCollapsed ? "opacity-0" : "opacity-100"
                )}>
                  Settings
                </span>
              </button>
              
              {/* Feature request button */}
              {!isCollapsed && (
                <a
                  href="https://pulseplan.featurebase.app/dashboard/posts"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors text-gray-400 hover:text-white hover:bg-neutral-700/50"
                >
                  <MessageSquarePlus size={18} className="flex-shrink-0" />
                  <span className={cn(
                    "text-sm font-medium whitespace-nowrap transition-opacity duration-200 ml-3",
                    isCollapsed ? "opacity-0" : "opacity-100"
                  )}>
                    Feature Request
                  </span>
                </a>
              )}
              
              {/* Help button */}
              {!isCollapsed && (
                <button className="w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors text-gray-400 hover:text-white hover:bg-neutral-700/50">
                  <HelpCircle size={18} className="flex-shrink-0" />
                  <span className={cn(
                    "text-sm font-medium whitespace-nowrap transition-opacity duration-200 ml-3",
                    isCollapsed ? "opacity-0" : "opacity-100"
                  )}>
                    Get help
                  </span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className={`flex flex-col w-full overflow-hidden ${isCollapsed ? 'md:ml-16' : 'md:ml-56'} transition-[margin-left] duration-300 ease-in-out`}>
        {/* Mobile header */}
        <div className="md:hidden bg-surface border-b border-gray-700 px-4 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-sm font-bold text-white">P</span>
              </div>
              <span className="ml-3 text-lg font-semibold text-textPrimary">
                PulsePlan
              </span>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main 
          className="flex-1 relative overflow-y-auto focus:outline-none"
          style={{
            scrollbarWidth: 'auto',
            scrollbarColor: 'rgba(75, 85, 99, 0.5) transparent'
          }}
        >
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>

        {/* Mobile bottom navigation */}
        <div className="md:hidden bg-surface border-t border-gray-700">
          <nav className="flex justify-around py-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex flex-col items-center py-2 px-3 rounded-lg text-xs font-medium transition-colors',
                    isActive
                      ? 'text-primary'
                      : 'text-textSecondary hover:text-textPrimary'
                  )}
                >
                  <item.icon className="h-5 w-5 mb-1" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Settings Modal */}
      <SettingsModal 
        isOpen={showSettings} 
        onClose={() => setShowSettings(false)} 
      />
    </div>
  )
}