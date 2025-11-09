import { useState, useEffect } from 'react'
import { X, Plus, MoreHorizontal, Edit3, Check, RefreshCw } from 'lucide-react'
import { useProfile } from '../hooks/useProfile'
import { supabase } from '../lib/supabase'
import { API_BASE_URL } from '../config/api'
import { canvasService } from '../services/canvasService'
import { cn } from '../lib/utils'
import { components, typography, spacing, colors, layout, cn as cnTokens } from '../lib/design-tokens'

type Props = {
  isOpen: boolean
  onClose: () => void
  integration: {
    id: string
    name: string
    icon: string
    category: string
  }
  onDisconnect: () => void
}

interface IntegrationSettings {
  id: string
  integration_id: string
  account_email?: string
  instructions?: string
  signature?: string
  settings: Record<string, any>
  created_at: string
  updated_at: string
}

export function ManageConnectionModal({ isOpen, onClose, integration, onDisconnect }: Props) {
  if (!isOpen) return null;
  
  const { data: profile } = useProfile()
  const [showDropdown, setShowDropdown] = useState(false)
  const [settings, setSettings] = useState<IntegrationSettings | null>(null)
  const [isEditingInstructions, setIsEditingInstructions] = useState(false)
  const [isEditingSignature, setIsEditingSignature] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [instructions, setInstructions] = useState('')
  const [signature, setSignature] = useState('')
  
  // Canvas-specific state
  const [canvasStatus, setCanvasStatus] = useState<any>(null)
  const [isSyncingCanvas, setIsSyncingCanvas] = useState(false)

  const handleBackdrop = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose()
  }

  // Load settings when modal opens
  useEffect(() => {
    if (isOpen && profile) {
      loadSettings()
      if (integration.id === 'canvas') {
        loadCanvasStatus()
      }
    }
  }, [isOpen, profile, integration.id])

  const loadSettings = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) return

      const response = await fetch(`${API_BASE_URL}/api/v1/integration-settings/${integration.id}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setSettings(data)
        setInstructions(data.instructions || '')
        setSignature(data.signature || '')
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
  }

  const saveSettings = async () => {
    if (!profile) return
    
    setIsSaving(true)
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) return

      const response = await fetch(`${API_BASE_URL}/api/v1/integration-settings/${integration.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          instructions,
          signature
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setSettings(data)
        setIsEditingInstructions(false)
        setIsEditingSignature(false)
      }
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const loadCanvasStatus = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) return

      const status = await canvasService.getIntegrationStatus()
      setCanvasStatus(status)
    } catch (error) {
      console.error('Failed to load Canvas status:', error)
    }
  }

  const handleCanvasSync = async () => {
    if (!profile) return
    
    setIsSyncingCanvas(true)
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) return

      const response = await fetch(`${API_BASE_URL}/api/v1/integrations/canvas/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        }
      })
      
      if (response.ok) {
        // Refresh Canvas status after sync
        await loadCanvasStatus()
      }
    } catch (error) {
      console.error('Failed to sync Canvas:', error)
    } finally {
      setIsSyncingCanvas(false)
    }
  }


  const getConnectedAccounts = () => {
    // Get real connected accounts - in real implementation, this would come from OAuth connections
    const accounts = []
    
    // For now, use the settings account email or a default
    if (settings?.account_email) {
      accounts.push({ email: settings.account_email, status: 'connected' })
    } else {
      // Fallback to user's email or a default
      const defaultEmail = profile?.email || 'user@example.com'
      accounts.push({ email: defaultEmail, status: 'connected' })
    }
    
    return accounts
  }

  const getInstructionsPlaceholder = () => {
    switch (integration.id) {
      case 'gmail':
        return 'Ex. "When I say email my boss, I mean john.doe@company.com"'
      case 'google-calendar':
        return 'Ex. "When I say schedule a meeting with the team, include Sarah and Mike"'
      case 'google-contacts':
        return 'Ex. "When I say call my mom, use the number from my contacts"'
      case 'canvas':
        return 'Ex. "When I say check my assignments, prioritize due this week"'
      case 'google-drive':
        return 'Ex. "When I say open my presentation, use the latest version"'
      case 'notion':
        return 'Ex. "When I say show my notes, include the project planning section"'
      default:
        return 'Ex. "When I say email my partner, I mean pepper.potts@example.com"'
    }
  }

  const formatLastSync = (lastSync: string): string => {
    const date = new Date(lastSync)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
    
    return date.toLocaleDateString()
  }


  const connectedAccounts = getConnectedAccounts()

  return (
    <div
      className={cnTokens(
        components.modal.overlay,
        'p-4 transition-all duration-300',
        isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
      )}
      onClick={handleBackdrop}
    >
      <div
        className={cnTokens(
          components.modal.container,
          'w-full max-w-lg max-h-[80vh] flex flex-col transition-all duration-300',
          isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {isOpen ? (
          <>
            {/* Header */}
        <div className={cnTokens(components.modal.header, 'flex items-center justify-between')}>
          <div className="flex items-center gap-2">
            <img
              src={integration.icon}
              alt={integration.name}
              className="w-5 h-5 object-contain"
            />
            <h2 className={components.modal.title}>{integration.name}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className={components.modal.closeButton}
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className={cnTokens(components.modal.content, 'overflow-y-auto flex-1')}>

          {/* Connected Accounts */}
          <div className={spacing.section.marginBottom}>
            <h3 className={cnTokens(typography.subsectionTitle, colors.text.primary, 'mb-3')}>
              {connectedAccounts.length} Connected Account{connectedAccounts.length !== 1 ? 's' : ''}
            </h3>
            <div className={spacing.stack.sm}>
              {connectedAccounts.map((account, index) => (
                <div
                  key={index}
                  className={components.connectionItem.base}
                >
                  <div className="flex items-center gap-3">
                    <div className={components.connectionItem.iconContainer}>
                      <img
                        src={integration.icon}
                        alt={integration.name}
                        className={components.connectionItem.icon}
                      />
                    </div>
                    <div>
                      <p className={components.connectionItem.text.primary}>{account.email}</p>
                      <p className={components.connectionItem.text.secondary}>Connected</p>
                    </div>
                  </div>
                  <div className="relative">
                    <button 
                      onClick={() => setShowDropdown(!showDropdown)}
                      className={components.connectionItem.actionButton}
                    >
                      <MoreHorizontal className="w-4 h-4 text-gray-400" />
                    </button>
                    {showDropdown && (
                      <div className={components.connectionItem.dropdown}>
                        <button
                          onClick={() => {
                            onDisconnect()
                            setShowDropdown(false)
                          }}
                          className={components.connectionItem.dropdownItem}
                        >
                          Disconnect
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Additional Instructions */}
          <div className={spacing.section.marginBottom}>
            <div className={cnTokens(layout.flex.between, 'mb-3')}>
              <h3 className={cnTokens(typography.subsectionTitle, colors.text.primary)}>Additional Instructions</h3>
              <button 
                onClick={isEditingInstructions ? saveSettings : () => setIsEditingInstructions(true)}
                className={components.iconButton.small}
                disabled={isSaving}
              >
                {isEditingInstructions ? (
                  <Check className="w-4 h-4 text-gray-400" />
                ) : (
                  <Edit3 className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
            <div className={components.settingItem.base}>
              <textarea
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder={getInstructionsPlaceholder()}
                className={cnTokens(components.textarea.base, 'w-full bg-transparent')}
                disabled={!isEditingInstructions}
                rows={3}
              />
            </div>
          </div>

          {/* Integration-specific sections */}
          {integration.id === 'gmail' && (
            <div className={spacing.section.marginBottom}>
            <div className={cnTokens(layout.flex.between, 'mb-3')}>
              <h3 className={cnTokens(typography.subsectionTitle, colors.text.primary)}>Email Signatures</h3>
              <button 
                onClick={isEditingSignature ? saveSettings : () => setIsEditingSignature(true)}
                className={components.iconButton.small}
                disabled={isSaving}
              >
                {isEditingSignature ? (
                  <Check className="w-4 h-4 text-gray-400" />
                ) : (
                  <Edit3 className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
            <div className={components.settingItem.base}>
              <textarea
                value={signature}
                onChange={(e) => setSignature(e.target.value)}
                placeholder="Enter your email signature..."
                className={cnTokens(components.textarea.base, 'w-full bg-transparent')}
                disabled={!isEditingSignature}
                rows={3}
              />
            </div>
            </div>
          )}

          {integration.id === 'google-calendar' && (
            <div className={spacing.section.marginBottom}>
              <div className={cnTokens(layout.flex.between, 'mb-3')}>
                <h3 className={cnTokens(typography.subsectionTitle, colors.text.primary)}>Calendar Settings</h3>
                <button className={components.iconButton.small}>
                  <Plus className="w-4 h-4 text-gray-400" />
                </button>
              </div>
              <div className={spacing.stack.sm}>
                <button
                  type="button"
                  className={cnTokens(components.settingItem.interactive, 'flex items-center justify-between w-full')}
                >
                  <span className={cnTokens(typography.body.default, colors.text.primary)}>
                    Make all my events between 9-5
                  </span>
                </button>
              </div>
            </div>
          )}

          {integration.id === 'canvas' && canvasStatus?.connected && (
            <div className={spacing.section.marginBottom}>
              <div className={cnTokens(layout.flex.between, 'mb-3')}>
                <h3 className={cnTokens(typography.subsectionTitle, colors.text.primary)}>Sync Status</h3>
                <button
                  onClick={handleCanvasSync}
                  disabled={isSyncingCanvas}
                  className={cnTokens(
                    components.button.base,
                    components.button.primary,
                    "px-3 py-1.5 flex items-center gap-2",
                    isSyncingCanvas && "opacity-70 cursor-not-allowed"
                  )}
                >
                  <RefreshCw className={cn("w-3 h-3", isSyncingCanvas && "animate-spin")} />
                  {isSyncingCanvas ? 'Syncing...' : 'Sync Now'}
                </button>
              </div>
              <div className={cnTokens(components.settingItem.base, spacing.stack.sm)}>
                <div className={layout.flex.between}>
                  <span className={cnTokens(typography.body.small, colors.text.secondary)}>Assignments Synced</span>
                  <span className={cnTokens(typography.body.default, colors.text.primary)}>{canvasStatus.totalCanvasTasks}</span>
                </div>
                <div className={layout.flex.between}>
                  <span className={cnTokens(typography.body.small, colors.text.secondary)}>Last Sync</span>
                  <span className={cnTokens(typography.body.small, colors.text.tertiary)}>
                    {canvasStatus.lastSync ? formatLastSync(canvasStatus.lastSync) : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={components.modal.footer}>
          <button
            onClick={onClose}
            className={cnTokens(components.button.base, components.button.secondary)}
          >
            Done
          </button>
        </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
