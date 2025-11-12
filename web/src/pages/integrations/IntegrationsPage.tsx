import { useState, useEffect } from 'react'
import { usePageTitle } from '@/hooks/ui'
import { useQueryClient } from '@tanstack/react-query'
import {
  Loader2
} from 'lucide-react'
import { InlineAlert } from '@/components/ui/InlineAlert'
import { toast } from '@/lib/toast'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { useOAuthConnections } from '@/hooks/integrations'
import type { OAuthProvider, OAuthService } from '@/services/integrations'
import { CanvasAPIConnectionModal } from '@/components/modals'
import { ManageConnectionModal } from '@/components/modals'
import { canvasService, type CanvasIntegrationStatus } from '@/services/integrations'
import { OAUTH_CACHE_KEYS } from '@/hooks/shared/cacheKeys'

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
  usePageTitle('Integrations')
  const queryClient = useQueryClient()
  const [connectingIntegration, setConnectingIntegration] = useState<string | null>(null)
  // Tracks a connection in-flight so we can keep UI loading until server reflects it
  const [pendingConnection, setPendingConnection] = useState<{ provider: OAuthProvider; service: OAuthService; integrationId: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showCanvasModal, setShowCanvasModal] = useState(false)
  const [showManageModal, setShowManageModal] = useState(false)
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [canvasStatus, setCanvasStatus] = useState<CanvasIntegrationStatus | null>(null)
  const { socket, isConnected: wsConnected } = useWebSocket()

  const {
    isLoading,
    connect,
    disconnect,
    isConnected,
    connectError,
    disconnectError,
    refetch: refetchConnections
  } = useOAuthConnections()

  const integrations: Integration[] = [
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
      id: 'outlook-calendar',
      name: 'Outlook Calendar',
      icon: '/assets/integrations/OutlookCalendar.svg',
      category: 'Calendar',
      provider: 'microsoft',
      service: 'calendar'
    },
    {
      id: 'apple-calendar',
      name: 'Apple Calendar',
      icon: '/assets/integrations/AppleCalendar.svg',
      category: 'Calendar',
      comingSoon: true
    },

    // Email
    {
      id: 'gmail',
      name: 'Gmail',
      icon: '/assets/integrations/Gmail.svg',
      category: 'Email',
      provider: 'google',
      service: 'gmail'
    },
    {
      id: 'outlook-mail',
      name: 'Outlook Mail',
      icon: '/assets/integrations/OutlookMail.svg',
      category: 'Email',
      provider: 'microsoft',
      service: 'outlook'
    },

    // Productivity
    {
      id: 'canvas',
      name: 'Canvas',
      icon: '/canvas.png',
      category: 'Productivity'
    },
    {
      id: 'google-drive',
      name: 'Google Drive',
      icon: '/assets/integrations/GoogleDrive.svg',
      category: 'Productivity',
      comingSoon: true
    },
    {
      id: 'notion',
      name: 'Notion',
      icon: '/assets/integrations/Notion.svg',
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
      icon: '/assets/integrations/AppleContacts.svg',
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
    if (integration.provider && integration.service) {
      setPendingConnection({ provider: integration.provider, service: integration.service, integrationId: integration.id })
      try {
        sessionStorage.setItem('oauth_in_progress', JSON.stringify({
          provider: integration.provider,
          service: integration.service,
          integrationId: integration.id,
          timestamp: Date.now()
        }))
      } catch {
        // Ignore sessionStorage errors
      }
    }

    try {
      const result = await connect(integration.provider, integration.service)
      if (!result.success) {
        setError(result.error || 'Failed to connect')
        setPendingConnection(null)
        setConnectingIntegration(null)
        try {
          sessionStorage.removeItem('oauth_in_progress')
        } catch {
          // Ignore sessionStorage errors
        }
        return
      }

      // WebSocket/postMessage will handle success notification
      // Don't clear loading states here - let WebSocket, postMessage, or cleanup timeout handle it
      // This ensures "Connecting..." shows until we actually get confirmation
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
      setPendingConnection(null)
      setConnectingIntegration(null)
      try {
        sessionStorage.removeItem('oauth_in_progress')
      } catch {
        // Ignore sessionStorage errors
      }
    }
  }

  const handleManage = (integration: Integration) => {
    setSelectedIntegration(integration)
    setShowManageModal(true)
  }

  const handleDisconnect = async (integration: Integration) => {
    setError(null)
    setConnectingIntegration(integration.id)

    try {
      if (integration.id === 'canvas') {
        await canvasService.disconnect()
        await loadCanvasStatus() // Refresh status after disconnect
        toast.success('Disconnected', `${integration.name} disconnected`)
      } else if (integration.provider && integration.service) {
        // Pass both provider AND service to disconnect only this specific service
        await disconnect(integration.provider, integration.service)

        // Single refetch after disconnect - backend will handle the state update
        await refetchConnections()
        toast.success('Disconnected', `${integration.name} disconnected`)
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
    if (!integration.provider || !integration.service) return 'coming-soon'

    // Check if this specific service is connected
    const connected = isConnected(integration.provider, integration.service)

    if (connectingIntegration === integration.id || (pendingConnection && pendingConnection.integrationId === integration.id)) {
      return 'connecting'
    }
    return connected ? 'connected' : 'disconnected'
  }

  const getStatusButton = (integration: Integration) => {
    const status = getIntegrationStatus(integration)
    const isCurrentlyConnecting = connectingIntegration === integration.id

    if (isCurrentlyConnecting || status === 'connecting') {
      const isDisconnecting = status === 'connected' && isCurrentlyConnecting
      return (
        <button disabled className="px-3 py-1.5 bg-neutral-800 text-white text-xs font-medium rounded-lg flex items-center gap-2">
          <Loader2 className="w-3 h-3 animate-spin" />
          {isDisconnecting ? 'Disconnecting...' : 'Connecting...'}
        </button>
      )
    }

    // Canvas now uses standard connected status with Manage button only

    switch (status) {
      case 'connected':
        return (
          <button
            onClick={() => handleManage(integration)}
            className="px-3 py-1.5 bg-neutral-800 text-white text-xs font-medium rounded-lg hover:bg-neutral-700 transition-colors"
          >
            Manage
          </button>
        )
      case 'disconnected':
        return (
          <button
            onClick={() => handleConnect(integration)}
            className="px-3 py-1.5 bg-white text-black text-xs font-medium rounded-lg hover:bg-gray-100 transition-colors"
          >
            Connect
          </button>
        )
      case 'coming-soon':
        return (
          <span className="text-gray-400 text-xs">
            Coming Soon
          </span>
        )
    }
  }

  const loadCanvasStatus = async () => {
    try {
      const status = await canvasService.getIntegrationStatus()
      setCanvasStatus(status)
    } catch (_error) {
      setCanvasStatus(null)
    }
  }

  // Listen for OAuth connection completion via WebSocket
  useEffect(() => {
    if (!socket || !wsConnected) return

    const handleOAuthConnected = async (message: Record<string, unknown>) => {
      const data = (message.data as Record<string, unknown>) || message

      // Invalidate and refetch connections immediately to update UI
      await queryClient.invalidateQueries({
        queryKey: OAUTH_CACHE_KEYS.CONNECTIONS,
        refetchType: 'all'
      })

      await refetchConnections()

      // Clear loading states
      setConnectingIntegration(null)
      setPendingConnection(null)

      // Clear sessionStorage markers
      try {
        sessionStorage.removeItem('oauth_in_progress')
        sessionStorage.removeItem('oauth_result')
      } catch {
        // Ignore sessionStorage errors
      }

      // Show success toast
      const provider = data.provider as string || 'Account'
      toast.success('Connected successfully', `${provider} account connected`)
    }

    socket.on('oauth_connected', handleOAuthConnected)
    return () => {
      socket.off('oauth_connected', handleOAuthConnected)
    }
  }, [socket, wsConnected, refetchConnections, queryClient])

  // Cleanup any pending poll when unmounting
  useEffect(() => {
    return () => {
      // No longer needed since we removed Canvas sync polling
    }
  }, [])

  useEffect(() => {
    loadCanvasStatus()
  }, [])

  // Cleanup timeout guard: Prevent orphaned pending connection states
  useEffect(() => {
    if (!pendingConnection) return

    const PENDING_CONNECTION_TIMEOUT = 30000 // 30 seconds max
    const timeout = setTimeout(() => {
      setPendingConnection(null)
      setConnectingIntegration(null)
      try {
        sessionStorage.removeItem('oauth_in_progress')
      } catch {
        // Ignore sessionStorage errors
      }
    }, PENDING_CONNECTION_TIMEOUT)

    return () => clearTimeout(timeout)
  }, [pendingConnection])

  // Listen for OAuth completion via postMessage and sessionStorage (simplified)
  useEffect(() => {
    const processedTimestamps = new Set<number>()

    const processOAuthResult = (result: Record<string, unknown>) => {
      // Validate result
      if (!result || !result.timestamp || !result.type) {
        return
      }

      // Prevent duplicate processing by checking timestamp
      const timestamp = result.timestamp as number
      if (processedTimestamps.has(timestamp)) {
        return
      }

      // Check if this is a recent event (within last 30 seconds)
      const age = Date.now() - timestamp
      if (age > 30000) {
        return
      }

      // Mark as processed BEFORE doing anything else
      processedTimestamps.add(timestamp)

      // Clear the sessionStorage item immediately to prevent re-processing
      try {
        sessionStorage.removeItem('oauth_result')
      } catch {
        // Ignore sessionStorage errors
      }

      if (result.type === 'oauth-success') {
        // Invalidate cache and refetch (fallback if WebSocket didn't fire)
        queryClient.invalidateQueries({
          queryKey: OAUTH_CACHE_KEYS.CONNECTIONS,
          refetchType: 'all'
        })

        refetchConnections()

        // Clear loading states
        setConnectingIntegration(null)
        setPendingConnection(null)

        // Clear both sessionStorage items to prevent reprocessing
        try {
          sessionStorage.removeItem('oauth_in_progress')
          sessionStorage.removeItem('oauth_result')
        } catch {
          // Ignore sessionStorage errors
        }
      } else if (result.type === 'oauth-error') {
        const errorMessage = (result.error as string) || 'Failed to connect account'
        toast.error('Connection failed', errorMessage)
        setConnectingIntegration(null)
        setPendingConnection(null)
        try {
          sessionStorage.removeItem('oauth_in_progress')
        } catch {
          // Ignore sessionStorage errors
        }
      }
    }

    const handleMessage = (event: MessageEvent) => {
      // Verify origin for security
      if (event.origin !== window.location.origin) {
        return
      }

      if (event.data.type === 'oauth-success' || event.data.type === 'oauth-error') {
        processOAuthResult(event.data)
      }
    }

    const handleStorageChange = (e: StorageEvent) => {
      // Storage event only fires in OTHER tabs/windows
      if (e.key === 'oauth_result' && e.newValue) {
        try {
          const result = JSON.parse(e.newValue)
          processOAuthResult(result)
        } catch {
          // Ignore parse errors
        }
      }
    }

    // On mount, if we see an OAuth in-progress marker (e.g., redirect flow), show loading immediately
    const inProgress = sessionStorage.getItem('oauth_in_progress')
    if (inProgress) {
      try {
        const parsed = JSON.parse(inProgress)
        if (parsed?.integrationId) {
          setConnectingIntegration(parsed.integrationId)
        }
      } catch {
        // Ignore parse errors
      }
    }

    // Check sessionStorage ONCE on mount only (no polling interval)
    // Only process if there's a corresponding oauth_in_progress marker (means OAuth is actually in flight)
    const result = sessionStorage.getItem('oauth_result')
    if (result && inProgress) { // Only process if OAuth was in progress
      try {
        const parsed = JSON.parse(result)
        const age = Date.now() - (parsed.timestamp || 0)
        if (age < 60000) { // Only process if less than 60 seconds old
          processOAuthResult(parsed)
        } else {
          sessionStorage.removeItem('oauth_result')
        }
      } catch {
        sessionStorage.removeItem('oauth_result')
      }
    } else if (result && !inProgress) {
      // Result exists but no in-progress marker - clean up orphaned result
      sessionStorage.removeItem('oauth_result')
    }

    window.addEventListener('message', handleMessage)
    window.addEventListener('storage', handleStorageChange)

    return () => {
      window.removeEventListener('message', handleMessage)
      window.removeEventListener('storage', handleStorageChange)
    }
  }, [refetchConnections, queryClient])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-neutral-900 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 text-white animate-spin mb-4" />
        <p className="text-gray-400">Loading integrations...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center" style={{ backgroundColor: '#0f0f0f' }}>
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
              message={(error as string) || (connectError as Error)?.message || (disconnectError as Error)?.message}
            />
          </div>
        )}

        {/* Integrations */}
        <div className="space-y-8">
          {Object.entries(groupedIntegrations).map(([category, categoryIntegrations]) => (
            <div key={category}>
              <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">{category}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {categoryIntegrations.map((integration) => {
                  return (
                    <div key={integration.id} className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-neutral-700 flex items-center justify-center overflow-hidden">
                          <img
                            src={integration.icon}
                            alt={integration.name}
                            className="w-8 h-8 object-contain"
                          />
                        </div>
                        <div>
                          <h3 className="text-white font-medium text-sm">{integration.name}</h3>
                        </div>
                      </div>
                      {getStatusButton(integration)}
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
        }}
      />
      {selectedIntegration && (
        <ManageConnectionModal
          isOpen={showManageModal}
          onClose={() => {
            setShowManageModal(false)
            setSelectedIntegration(null)
          }}
          integration={selectedIntegration}
          onDisconnect={() => {
            handleDisconnect(selectedIntegration)
            setShowManageModal(false)
            setSelectedIntegration(null)
          }}
        />
      )}
    </div>
  )
}
