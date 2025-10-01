import { useState, useEffect } from 'react'
import {
  Loader2,
  AlertCircle,
  RefreshCw,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { InlineAlert } from '../components/ui/InlineAlert'
import { cn } from '../lib/utils'
import { toast } from '../lib/toast'
import { useWebSocket } from '../contexts/WebSocketContext'
import { useOAuthConnections } from '../hooks/useOAuthConnections'
import type { OAuthProvider, OAuthService } from '../services/oauthService'
import { CanvasAPIConnectionModal } from '../components/CanvasAPIConnectionModal'
import { canvasService, type CanvasIntegrationStatus, formatLastSync } from '../services/canvasService'

interface Integration {
  id: string
  name: string
  icon: string
  category: string
  provider?: OAuthProvider
  service?: OAuthService
  comingSoon?: boolean
}

export function IntegrationsPage() {
  const [connectingIntegration, setConnectingIntegration] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showCanvasModal, setShowCanvasModal] = useState(false)
  const [canvasStatus, setCanvasStatus] = useState<CanvasIntegrationStatus | null>(null)
  const [isSyncingCanvas, setIsSyncingCanvas] = useState(false)
  const [syncProgress, setSyncProgress] = useState<{
    coursesProcessed: number
    totalCourses: number
    assignmentsSynced: number
    status: 'starting' | 'in_progress' | 'completed' | 'error'
    message?: string
  } | null>(null)
  const [isPollingStatus, setIsPollingStatus] = useState(false)
  const [pollTimer, setPollTimer] = useState<ReturnType<typeof setTimeout> | null>(null)
  const { socket, isConnected: wsConnected } = useWebSocket()

  const {
    isLoading,
    connect,
    disconnect,
    isConnected,
    connectError,
    disconnectError
  } = useOAuthConnections()

  const integrations: Integration[] = [
    // Email
    {
      id: 'gmail',
      name: 'Gmail',
      icon: '/gmail.png',
      category: 'Email',
      provider: 'google',
      service: 'gmail'
    },
    {
      id: 'outlook-mail',
      name: 'Outlook Mail',
      icon: '/applecalendar.png',
      category: 'Email',
      provider: 'microsoft',
      service: 'outlook'
    },

    // Calendar
    {
      id: 'google-calendar',
      name: 'Google Calendar',
      icon: '/googlecalendar.png',
      category: 'Calendar',
      provider: 'google',
      service: 'calendar'
    },
    {
      id: 'apple-calendar',
      name: 'Apple Calendar',
      icon: '/applecalendar.png',
      category: 'Calendar',
      comingSoon: true
    },
    {
      id: 'outlook-calendar',
      name: 'Outlook Calendar',
      icon: '/applecalendar.png',
      category: 'Calendar',
      provider: 'microsoft',
      service: 'calendar'
    },

    // Productivity
    {
      id: 'canvas',
      name: 'Canvas',
      icon: '/canvas.png',
      category: 'Productivity'
    },
    {
      id: 'notion',
      name: 'Notion',
      icon: '/notion.png',
      category: 'Productivity',
      comingSoon: true
    },

    // Messaging & Contacts
    {
      id: 'google-contacts',
      name: 'Google Contacts',
      icon: '/googlecontacts.webp',
      category: 'Messaging & Contacts',
      provider: 'google',
      service: 'contacts'
    },
    {
      id: 'apple-contacts',
      name: 'Apple Contacts',
      icon: '/applecontacts.webp',
      category: 'Messaging & Contacts',
      comingSoon: true
    },
  ]

  const groupedIntegrations = integrations.reduce((acc, integration) => {
    if (!acc[integration.category]) {
      acc[integration.category] = []
    }
    acc[integration.category].push(integration)
    return acc
  }, {} as Record<string, Integration[]>)

  const handleConnect = async (integration: Integration) => {
    if (integration.id === 'canvas') {
      setShowCanvasModal(true)
      return
    }
    if (!integration.provider || !integration.service) return

    setError(null)
    setConnectingIntegration(integration.id)

    try {
      const result = await connect(integration.provider, integration.service)
      if (!result.success) {
        setError(result.error || 'Failed to connect')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
    } finally {
      setConnectingIntegration(null)
    }
  }

  const handleDisconnect = async (integration: Integration) => {
    setError(null)
    setConnectingIntegration(integration.id)

    try {
      if (integration.id === 'canvas') {
        await canvasService.disconnect()
        await loadCanvasStatus() // Refresh status after disconnect
      } else if (integration.provider) {
        await disconnect(integration.provider)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
    } finally {
      setConnectingIntegration(null)
    }
  }

  const getIntegrationStatus = (integration: Integration) => {
    if (integration.id === 'canvas') {
      return canvasStatus?.connected ? 'connected' : 'disconnected'
    }
    if (integration.comingSoon) return 'coming-soon'
    if (!integration.provider) return 'coming-soon'
    return isConnected(integration.provider) ? 'connected' : 'disconnected'
  }

  const getStatusButton = (integration: Integration) => {
    const status = getIntegrationStatus(integration)
    const isCurrentlyConnecting = connectingIntegration === integration.id

    if (isCurrentlyConnecting) {
      return (
        <button disabled className="px-3 py-1.5 border border-gray-400 text-white text-xs font-medium rounded-md flex items-center gap-2">
          <Loader2 className="w-3 h-3 animate-spin" />
          {status === 'connected' ? 'Disconnecting...' : 'Connecting...'}
        </button>
      )
    }

    // Special handling for Canvas with sync functionality
    if (integration.id === 'canvas' && status === 'connected') {
      return (
        <div className="flex items-center gap-2">
          <button
            onClick={handleCanvasSync}
            disabled={isSyncingCanvas}
            className={cn(
              "px-3 py-1.5 text-white text-xs font-medium rounded-md transition-colors flex items-center gap-2",
              isSyncingCanvas 
                ? "bg-blue-600 cursor-not-allowed opacity-70"
                : "bg-blue-600 hover:bg-blue-700"
            )}
          >
            <RefreshCw className={cn("w-3 h-3", isSyncingCanvas && "animate-spin")} />
            {isSyncingCanvas ? 'Syncing...' : 'Sync'}
          </button>
          <button
            onClick={() => handleDisconnect(integration)}
            className="px-3 py-1.5 border border-gray-400 text-white text-xs font-medium rounded-md hover:bg-gray-800 transition-colors"
          >
            Disconnect
          </button>
        </div>
      )
    }

    switch (status) {
      case 'connected':
        return (
          <button
            onClick={() => handleDisconnect(integration)}
            className="px-3 py-1.5 border border-gray-400 text-white text-xs font-medium rounded-md hover:bg-gray-800 transition-colors"
          >
            Disconnect
          </button>
        )
      case 'disconnected':
        return (
          <button
            onClick={() => handleConnect(integration)}
            className="px-3 py-1.5 bg-white text-black text-xs font-medium rounded-md hover:bg-gray-100 transition-colors"
          >
            Connect
          </button>
        )
      case 'coming-soon':
        return (
          <span className="px-3 py-1.5 bg-neutral-800 text-gray-500 text-xs font-medium rounded-md">
            Coming Soon
          </span>
        )
    }
  }

  const loadCanvasStatus = async () => {
    try {
      const status = await canvasService.getIntegrationStatus()
      setCanvasStatus(status)
    } catch (e) {
      setCanvasStatus(null)
    }
  }

  // Begin watching for backfill completion via WebSocket
  const beginCanvasSyncWatch = () => {
    setIsSyncingCanvas(true)
    setSyncProgress({
      coursesProcessed: 0,
      totalCourses: 0,
      assignmentsSynced: 0,
      status: 'in_progress',
      message: 'Fetching courses and assignments from Canvas...'
    })
  }

  // Listen for Canvas sync completion via WebSocket
  useEffect(() => {
    if (!socket || !wsConnected) return

    const handleCanvasSync = (message: any) => {
      console.log('Canvas sync event received:', message)
      if (!message) return

      // Backend emits: { user_id, event_type, data: { status, ... }, timestamp }
      const eventData = message.data || message
      console.log('Event data extracted:', eventData)
      console.log('Status:', eventData.status)
      
      if (eventData.status === 'completed') {
        console.log('✅ Handling completion event')
        const assignmentsUpserted = eventData.assignments_upserted || 0
        const coursesProcessed = eventData.courses_processed || 0
        setSyncProgress({
          coursesProcessed: coursesProcessed,
          totalCourses: coursesProcessed,
          assignmentsSynced: assignmentsUpserted,
          status: 'completed',
          message: eventData.message || `Sync completed! ${assignmentsUpserted} assignments synced.`
        })
        toast.success('Canvas sync completed', `${assignmentsUpserted} assignments available.`)
        
        setTimeout(() => {
          console.log('⏰ Clearing sync state after 2s delay')
          setSyncProgress(null)
          setIsSyncingCanvas(false)
          loadCanvasStatus()
        }, 2000)
      } else if (eventData.status === 'error' || eventData.status === 'failed') {
        setSyncProgress({
          coursesProcessed: 0,
          totalCourses: 0,
          assignmentsSynced: 0,
          status: 'error',
          message: eventData.message || 'Sync failed. Please try again.'
        })
        toast.error('Canvas sync failed', eventData.message || 'Unexpected error')
        
        setTimeout(() => {
          setSyncProgress(null)
          setIsSyncingCanvas(false)
        }, 4000)
      }
    }

    socket.on('canvas_sync', handleCanvasSync)
    return () => {
      socket.off('canvas_sync', handleCanvasSync)
    }
  }, [socket, wsConnected])

  const handleCanvasSync = async () => {
    if (!canvasStatus?.connected) return

    try {
      setIsSyncingCanvas(true)
      if (isPollingStatus && pollTimer) {
        clearTimeout(pollTimer)
        setPollTimer(null)
      }
      setIsPollingStatus(false)
      const shouldShowToast = () => {
        const hidden = document.visibilityState !== 'visible'
        const offPage = !window.location.pathname.toLowerCase().includes('integrations')
        return hidden || offPage
      }
      if (shouldShowToast()) {
        toast.loading('Canvas Sync', 'Starting Canvas sync...')
      }
      setSyncProgress({
        coursesProcessed: 0,
        totalCourses: 0,
        assignmentsSynced: 0,
        status: 'starting',
        message: 'Starting Canvas sync...'
      })

      await canvasService.triggerSync('full')
      
      // Move to in-progress visual state
      setSyncProgress(prev => ({
        ...prev!,
        status: 'in_progress',
        message: 'Fetching courses and assignments from Canvas...'
      }))

      // Bounded polling fallback (prefer WebSocket in future)
      const previousTotal = canvasStatus?.totalCanvasTasks || 0
      const maxAttempts = 30 // ~60s at 2s interval
      let attempts = 0
      if (isPollingStatus) {
        // Already polling; do not start another loop
        return
      }
      setIsPollingStatus(true)

      const pollForCompletion = async () => {
        attempts += 1
        try {
          const status = await canvasService.getIntegrationStatus()
          const increased = status.totalCanvasTasks > previousTotal
          const lastSyncChanged = status.lastSync !== canvasStatus?.lastSync
          if (increased || lastSyncChanged) {
            setSyncProgress({
              coursesProcessed: 1,
              totalCourses: 1,
              assignmentsSynced: status.totalCanvasTasks,
              status: 'completed',
              message: `Sync completed! ${status.totalCanvasTasks} assignments synced.`
            })
            if (shouldShowToast()) {
              toast.success('Canvas Sync Completed', `${status.totalCanvasTasks} assignments available.`)
            }
            setIsPollingStatus(false)
            if (pollTimer) {
              clearTimeout(pollTimer)
              setPollTimer(null)
            }
            setTimeout(() => {
              setSyncProgress(null)
              loadCanvasStatus()
            }, 2000)
          } else if (attempts < maxAttempts) {
            const t = setTimeout(pollForCompletion, 2000)
            setPollTimer(t)
          } else {
            // Timed out
            setSyncProgress(prev => ({
              ...prev!,
              status: 'error',
              message: 'Sync timed out. Please try again.'
            }))
            if (shouldShowToast()) {
              toast.error('Canvas Sync Timed Out', 'Please try again shortly.')
            }
            setIsPollingStatus(false)
            if (pollTimer) {
              clearTimeout(pollTimer)
              setPollTimer(null)
            }
            setTimeout(() => setSyncProgress(null), 4000)
          }
        } catch (e) {
          setSyncProgress(prev => ({
            ...prev!,
            status: 'error',
            message: 'Sync failed. Please try again.'
          }))
          if (shouldShowToast()) {
            toast.error('Canvas Sync Failed', e instanceof Error ? e.message : 'Unexpected error')
          }
          setIsPollingStatus(false)
          if (pollTimer) {
            clearTimeout(pollTimer)
            setPollTimer(null)
          }
          setTimeout(() => setSyncProgress(null), 4000)
        }
      }

      const t = setTimeout(pollForCompletion, 2000)
      setPollTimer(t)
    } catch (e) {
      setSyncProgress({
        coursesProcessed: 0,
        totalCourses: 0,
        assignmentsSynced: 0,
        status: 'error',
        message: e instanceof Error ? e.message : 'Sync failed'
      })
      const hidden = document.visibilityState !== 'visible'
      const offPage = !window.location.pathname.toLowerCase().includes('integrations')
      if (hidden || offPage) {
        toast.error('Canvas Sync Failed', e instanceof Error ? e.message : 'Unexpected error')
      }
      setTimeout(() => setSyncProgress(null), 5000)
    } finally {
      setIsSyncingCanvas(false)
    }
  }

  // Cleanup any pending poll when unmounting
  useEffect(() => {
    return () => {
      if (pollTimer) {
        clearTimeout(pollTimer)
      }
    }
  }, [pollTimer])

  useEffect(() => {
    loadCanvasStatus()
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-neutral-900 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 text-white animate-spin mb-4" />
        <p className="text-gray-400">Loading integrations...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neutral-900 flex flex-col items-center">
      <div className="w-full max-w-4xl px-6 pt-24 pb-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-white">Integrations</h1>
        </div>

        {/* Error Alert */}
        {(error || connectError || disconnectError) && (
          <div className="mb-6">
            <InlineAlert
              variant="error"
              title="Connection Error"
              message={(error as string) || (connectError as any)?.message || (disconnectError as any)?.message}
            />
          </div>
        )}

        {/* Canvas Sync Progress Alert */}
        {syncProgress && (
          <div className={cn(
            "mb-6 p-4 rounded-xl flex items-center gap-3",
            syncProgress.status === 'completed' && "bg-green-600 text-white",
            syncProgress.status === 'error' && "bg-red-600 text-white",
            (syncProgress.status === 'in_progress' || syncProgress.status === 'starting') && "bg-blue-600 text-white"
          )}>
            {syncProgress.status === 'completed' && <CheckCircle className="w-5 h-5 text-white flex-shrink-0" />}
            {syncProgress.status === 'error' && <XCircle className="w-5 h-5 text-white flex-shrink-0" />}
            {(syncProgress.status === 'in_progress' || syncProgress.status === 'starting') && (
              <Loader2 className="w-5 h-5 text-white flex-shrink-0 animate-spin" />
            )}
            <div className="flex-1">
              <p className="text-sm font-medium">
                Canvas Sync {syncProgress.status === 'completed' ? 'Completed' : syncProgress.status === 'error' ? 'Failed' : 'In Progress'}
              </p>
              <p className="text-white/80 text-xs">
                {syncProgress.message}
              </p>
              {syncProgress.status === 'in_progress' && syncProgress.totalCourses > 0 && (
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-white/80 mb-1">
                    <span>Progress</span>
                    <span>{syncProgress.coursesProcessed}/{syncProgress.totalCourses} courses</span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-1.5">
                    <div 
                      className="bg-white h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${(syncProgress.coursesProcessed / syncProgress.totalCourses) * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Integrations */}
        <div className="space-y-8">
          {Object.entries(groupedIntegrations).map(([category, categoryIntegrations]) => (
            <div key={category}>
              <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">{category}</h2>
              <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl overflow-hidden">
                {categoryIntegrations.map((integration, index) => {
                  const status = getIntegrationStatus(integration)
                  return (
                    <div key={integration.id}>
                      <div className="flex items-center justify-between p-4">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg bg-neutral-700 flex items-center justify-center overflow-hidden">
                            <img
                              src={integration.icon}
                              alt={integration.name}
                              className="w-8 h-8 object-contain"
                            />
                          </div>
                          <div>
                            <h3 className="text-white font-medium">{integration.name}</h3>
                            <div className="flex items-center gap-2 mt-1">
                                      {status === 'connected' && (
                                        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                                      )}
                                      <span className={cn(
                                        "text-xs capitalize",
                                        status === 'connected' ? 'text-green-400' : 'text-gray-400'
                                      )}>
                                        {status.replace('-', ' ')}
                                      </span>
                              {integration.id === 'canvas' && canvasStatus?.connected && (
                                <span className="text-xs text-gray-400">
                                Last sync: {formatLastSync(canvasStatus.lastSync)}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        {getStatusButton(integration)}
                      </div>
                      {index < categoryIntegrations.length - 1 && (
                        <div className="h-px bg-gray-700 mx-4"></div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
      <CanvasAPIConnectionModal
        isOpen={showCanvasModal}
        onClose={() => setShowCanvasModal(false)}
        onConnected={async () => {
          setShowCanvasModal(false)
          // Update status immediately to show "connected" and "disconnect" button
          setCanvasStatus({
            connected: true,
            lastSync: null,
            totalCanvasTasks: 0
          })
          // Begin watching initial backfill progress so user sees syncing UI
          beginCanvasSyncWatch()
        }}
      />
    </div>
  )
}
