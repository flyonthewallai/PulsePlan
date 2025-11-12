import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import {
  Home,
  CalendarDays,
  Settings,
  HelpCircle,
  ListTodo,
  Link2,
  ChevronDown,
  PanelLeft,
  LogOut,
  Gift,
  Users,
  Sparkles,
  BrainCircuit,
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { typography, colors, components, cn as cnTokens } from '../../lib/design-tokens'
import { ErrorBoundary } from '../ui/ErrorBoundary'
import { SettingsModal } from '../modals'
import { ReferralModal } from '../modals'
import { AmbassadorModal } from '../modals'
import { useAuthWebSocket } from '@/hooks/ui'
import { ProfilePicture } from '../ui/ProfilePicture'
import { useProfile } from '@/hooks/profile'

interface AppShellProps {
  children: React.ReactNode
}

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Calendar', href: '/calendar', icon: CalendarDays },
  { name: 'Taskboard', href: '/taskboard', icon: ListTodo },
  { name: 'Integrations', href: '/integrations', icon: Link2 },
]

export function AppShell({ children }: AppShellProps) {
  const location = useLocation()
  const navigate = useNavigate()

  // Persist collapsed state across reloads so the UI feels stable
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('sidebarCollapsed') : null
    return saved ? saved === 'true' : true
  })
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', String(isCollapsed))
    // Dispatch custom event for same-tab updates
    window.dispatchEvent(new CustomEvent('sidebarToggle'))
    // Set CSS variable for consumers (e.g., floating buttons) to position relative to sidebar
    const widthValue = isCollapsed ? '4rem' : '14rem'
    document.documentElement.style.setProperty('--sidebar-width', widthValue)
  }, [isCollapsed])

  const [showSettings, setShowSettings] = useState(false)
  const [showProfileModal, setShowProfileModal] = useState(false)
  const [showReferralModal, setShowReferralModal] = useState(false)
  const [showAmbassadorModal, setShowAmbassadorModal] = useState(false)
  const [settingsInitialSection, setSettingsInitialSection] = useState<'profile' | 'personalization' | undefined>(undefined)

  const profileAnchorRef = useRef<HTMLButtonElement | null>(null)
  const profileModalRef = useRef<HTMLDivElement | null>(null)
  const [isHoveringCollapsed, setIsHoveringCollapsed] = useState(false)

  // Initialize WebSocket connection with user authentication
  useAuthWebSocket()

  // Get user profile data
  const { data: profile } = useProfile()

  // Close the profile modal on outside click or on route change
  useEffect(() => {
    if (!showProfileModal) return
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node
      const clickedAnchor = profileAnchorRef.current?.contains(t)
      const clickedInside = profileModalRef.current?.contains(t)
      if (!clickedAnchor && !clickedInside) setShowProfileModal(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [showProfileModal])

  useEffect(() => {
    // Any navigation change closes the profile menu so it never lingers
    setShowProfileModal(false)
  }, [location.pathname])

  // Keyboard UX: ESC closes the menu
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowProfileModal(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

  // Helper to compute active state for nested routes
  const isPathActive = useCallback(
    (href: string) => location.pathname === href || location.pathname.startsWith(href + '/'),
    [location.pathname]
  )

  // Memoize sidebar classes to avoid reflows
  const sidebarWidthClass = useMemo(() => (isCollapsed ? 'md:w-16' : 'md:w-56'), [isCollapsed])
  const mainPadClass = useMemo(() => (isCollapsed ? 'md:pl-16' : 'md:pl-56'), [isCollapsed])

  return (
    <div className="min-h-screen overflow-x-hidden" style={{ backgroundColor: '#0f0f0f' }}>
      {/* Sidebar */}
      <aside className={cn('hidden md:flex md:flex-col h-screen fixed left-0 top-0 z-20 transition-[width] duration-200 ease-out overflow-hidden', sidebarWidthClass)}>
        <div className="flex flex-col h-full w-full border-r border-neutral-800" style={{ backgroundColor: '#0f0f0f' }}>
          {/* Sidebar header: collapse toggle + profile */}
          <div className="px-3 py-4 relative">
            {isCollapsed ? (
              /* Collapsed state: Show profile picture that changes to sidebar icon on hover, centered */
              <div className="flex justify-center">
                <button
                  type="button"
                  aria-label="Expand sidebar"
                  onClick={() => setIsCollapsed(false)}
                  onMouseEnter={() => setIsHoveringCollapsed(true)}
                  onMouseLeave={() => setIsHoveringCollapsed(false)}
                  className="relative flex h-8 w-8 items-center justify-center rounded-lg text-gray-300 hover:text-white hover:bg-neutral-700/50 transition-all duration-200"
                >
                  <div
                    className={cn(
                      'absolute inset-0 flex items-center justify-center transition-opacity duration-200',
                      isHoveringCollapsed ? 'opacity-0' : 'opacity-100'
                    )}
                  >
                    <ProfilePicture name={profile?.full_name} email={profile?.email} size="sm" />
                  </div>
                  <div
                    className={cn(
                      'absolute inset-0 flex items-center justify-center transition-opacity duration-200',
                      isHoveringCollapsed ? 'opacity-100' : 'opacity-0'
                    )}
                  >
                    <PanelLeft size={18} />
                  </div>
                </button>
              </div>
            ) : (
              /* Expanded state: Show profile button on left and collapse toggle on right */
              <div className="flex items-center gap-2 relative">
                {/* Profile anchor */}
                <button
                  ref={profileAnchorRef}
                  type="button"
                  onClick={() => setShowProfileModal((s) => !s)}
                  className="group flex items-center flex-1 h-8 px-2 rounded-lg transition hover:bg-neutral-700/40"
                  aria-expanded={showProfileModal}
                  aria-controls="profile-menu"
                >
                  <ProfilePicture name={profile?.full_name} email={profile?.email} size="sm" />
                  <span className="ml-2 text-white font-semibold text-sm truncate max-w-[120px]">
                    {profile?.full_name || profile?.email?.split('@')[0] || 'User'}
                  </span>
                  <ChevronDown
                    size={16}
                    className="ml-1 shrink-0 text-gray-400 group-hover:text-white transition-colors"
                  />
                </button>

                {/* Collapse toggle */}
                <button
                  type="button"
                  aria-label="Collapse sidebar"
                  onClick={() => setIsCollapsed(true)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-300 hover:text-white hover:bg-neutral-700/50 transition shrink-0"
                >
                  <PanelLeft size={18} />
                </button>
              </div>
            )}
            {/* Profile Modal */}
            {showProfileModal && !isCollapsed && (
              <div
                id="profile-menu"
                ref={profileModalRef}
                role="menu"
                className="absolute top-full left-0 mt-1 rounded-lg border border-gray-700/50 shadow-xl z-50 w-56"
                style={{ backgroundColor: '#1a1a1a' }}
              >
                {/* User Info */}
                <div className="px-3 py-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <ProfilePicture name={profile?.full_name} email={profile?.email} size="sm" />
                    <div className="min-w-0">
                      <p className="text-white text-sm font-medium truncate">
                        {profile?.full_name || 'User'}
                      </p>
                      <p className="text-gray-400 text-xs truncate">{profile?.email}</p>
                    </div>
                  </div>
                </div>

                {/* Divider */}
                <div className={cnTokens("px-3", components.divider.horizontal)}></div>

                {/* Menu Items */}
                <div className="py-1">
                  <button 
                    onClick={() => navigate('/pricing')}
                    className={cnTokens("w-full flex items-center gap-3 px-3 py-2 text-left", typography.body.default, colors.text.secondary, "hover:bg-neutral-700 hover:text-white transition-colors")}
                  >
                    <Sparkles size={16} className="text-white" />
                    <span>Upgrade plan</span>
                  </button>
                  <button
                    onClick={() => {
                      setSettingsInitialSection('personalization')
                      setShowSettings(true)
                      setShowProfileModal(false)
                    }}
                    className={cnTokens("w-full flex items-center gap-3 px-3 py-2 text-left", typography.body.default, colors.text.secondary, "hover:bg-neutral-700 hover:text-white transition-colors")}
                  >
                    <BrainCircuit size={16} className="text-white" />
                    <span>Personalization</span>
                  </button>
                  <button
                    onClick={() => {
                      setSettingsInitialSection(undefined)
                      setShowSettings(true)
                      setShowProfileModal(false)
                    }}
                    className={cnTokens("w-full flex items-center gap-3 px-3 py-2 text-left", typography.body.default, colors.text.secondary, "hover:bg-neutral-700 hover:text-white transition-colors")}
                  >
                    <Settings size={16} className="text-white" />
                    <span>Settings</span>
                  </button>
                </div>

                {/* Divider */}
                <div className={cnTokens("px-3", components.divider.horizontal)}></div>

                {/* Bottom Items */}
                <div className="py-1">
                  <button className="w-full flex items-center gap-3 px-3 py-2 text-left text-gray-300 hover:bg-neutral-700 hover:text-white transition-colors">
                    <HelpCircle size={16} className="text-white" />
                    <span className="text-sm">Help</span>
                    <ChevronDown size={12} className="text-gray-400 ml-auto" />
                  </button>
                  <button className="w-full flex items-center gap-3 px-3 py-2 text-left text-gray-300 hover:bg-neutral-700 hover:text-white transition-colors">
                    <LogOut size={16} className="text-white" />
                    <span className="text-sm">Log out</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 pb-3 space-y-1 overflow-y-auto">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'w-full flex items-center px-3 py-2 rounded-lg text-left transition-all duration-150 ease-out',
                    (isActive || isPathActive(item.href))
                      ? 'text-active font-semibold hover:bg-neutral-700/40'
                      : 'text-gray-400 hover:text-white hover:bg-neutral-700/40'
                  )
                }
                end={item.href === '/'}
              >
                {({ isActive }) => (
                  <>
                    <item.icon
                      size={18}
                      className={cn('flex-shrink-0', (isActive || isPathActive(item.href)) && 'text-active')}
                    />
                    <span
                      className={cn(
                        'text-sm whitespace-nowrap transition-opacity duration-150 ml-2',
                        isCollapsed ? 'opacity-0' : 'opacity-100'
                      )}
                    >
                      {item.name}
                    </span>
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          {/* Divider */}
          <div className="mx-3 border-t border-gray-700/50" />

          {/* Bottom Icons */}
          <div className="mt-auto p-3">
            {isCollapsed ? (
              <div className="flex justify-center">
                <div className="flex flex-col space-y-2">
                  <button 
                    onClick={() => setShowReferralModal(true)}
                    className="p-2 text-gray-400 hover:text-white hover:bg-neutral-700/40 rounded-lg transition-all duration-150 ease-out"
                    aria-label="Share with friends"
                  >
                    <Gift size={18} />
                  </button>
                  <button 
                    onClick={() => setShowAmbassadorModal(true)}
                    className="p-2 text-gray-400 hover:text-white hover:bg-neutral-700/40 rounded-lg transition-all duration-150 ease-out"
                    aria-label="Become an ambassador"
                  >
                    <Users size={18} />
                  </button>
                  <button className="p-2 text-gray-400 hover:text-white hover:bg-neutral-700/40 rounded-lg transition-all duration-150 ease-out">
                    <HelpCircle size={18} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => setShowReferralModal(true)}
                  className="p-2 text-gray-400 hover:text-white hover:bg-neutral-700/40 rounded-lg transition-all duration-150 ease-out"
                  aria-label="Share with friends"
                >
                  <Gift size={18} />
                </button>
                <button 
                  onClick={() => setShowAmbassadorModal(true)}
                  className="p-2 text-gray-400 hover:text-white hover:bg-neutral-700/40 rounded-lg transition-all duration-150 ease-out"
                  aria-label="Become an ambassador"
                >
                  <Users size={18} />
                </button>
                <div className="flex-1" />
                <button className="p-2 text-gray-400 hover:text-white hover:bg-neutral-700/40 rounded-lg transition-all duration-150 ease-out">
                  <HelpCircle size={18} />
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className={cn('bg-neutral-950 transition-[padding] duration-200 ease-out', mainPadClass)}>
        <main className="flex-1">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>

        {/* Mobile bottom navigation */}
        <div className="md:hidden fixed bottom-0 left-0 right-0 border-t border-gray-700 flex justify-around z-30" style={{ backgroundColor: '#0f0f0f' }}>
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex flex-col items-center py-2 px-3 rounded-lg text-xs font-medium transition-colors',
                  (isActive || isPathActive(item.href)) ? 'text-primary' : 'text-textSecondary hover:text-textPrimary'
                )
              }
              end={item.href === '/'}
            >
              <item.icon className="h-5 w-5 mb-1" />
              {item.name}
            </NavLink>
          ))}
        </div>
      </div>

      {/* Settings Modal */}
      <SettingsModal 
        isOpen={showSettings} 
        onClose={() => {
          setShowSettings(false)
          setSettingsInitialSection(undefined)
        }}
        initialSection={settingsInitialSection}
      />

      {/* Referral Modal */}
      <ReferralModal 
        isOpen={showReferralModal} 
        onClose={() => setShowReferralModal(false)} 
      />

      {/* Ambassador Modal */}
      <AmbassadorModal 
        isOpen={showAmbassadorModal} 
        onClose={() => setShowAmbassadorModal(false)} 
      />
    </div>
  )
}
