import React, { useState } from 'react'
import {
  Check,
  ChevronRight,
  Mail,
  Calendar,
  CheckSquare,
  Bell,
  FileText,
  Phone,
  Newspaper,
  Settings,
  Grid3X3,
  Gift,
  MessageCircle,
  HelpCircle,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { cn } from '../lib/utils'
import { useOAuthConnections } from '../hooks/useOAuthConnections'
import type { OAuthProvider, OAuthService } from '../services/oauthService'

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

  const {
    connections,
    isLoading,
    connect,
    disconnect,
    isConnected,
    isConnecting,
    isDisconnecting,
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
      category: 'Productivity',
      comingSoon: true
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
    if (!integration.provider) return

    setError(null)
    setConnectingIntegration(integration.id)

    try {
      await disconnect(integration.provider)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
    } finally {
      setConnectingIntegration(null)
    }
  }

  const getIntegrationStatus = (integration: Integration) => {
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
          <div className="mb-6 p-4 bg-red-900/20 border border-red-700/50 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div>
              <p className="text-red-400 text-sm font-medium">Connection Error</p>
              <p className="text-red-300 text-xs">
                {error || connectError?.message || disconnectError?.message}
              </p>
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
    </div>
  )
}
