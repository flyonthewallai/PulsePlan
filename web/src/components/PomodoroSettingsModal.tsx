import React, { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { components, typography, spacing, colors, cn } from '../lib/design-tokens'

interface PomodoroSettings {
  defaultDuration: number
  defaultBreak: number
  cyclesPerSession: number
  autoStartNextSession: boolean
  autoStartBreaks: boolean
  playSoundOnComplete: boolean
  desktopNotifications: boolean
}

interface PomodoroSettingsModalProps {
  isOpen: boolean
  onClose: () => void
  settings: PomodoroSettings
  onSave: (settings: PomodoroSettings) => void
}

const DEFAULT_SETTINGS: PomodoroSettings = {
  defaultDuration: 25,
  defaultBreak: 5,
  cyclesPerSession: 4,
  autoStartNextSession: false,
  autoStartBreaks: true,
  playSoundOnComplete: true,
  desktopNotifications: true,
}

export function PomodoroSettingsModal({ isOpen, onClose, settings, onSave }: PomodoroSettingsModalProps) {
  const [localSettings, setLocalSettings] = useState<PomodoroSettings>(settings)

  useEffect(() => {
    setLocalSettings(settings)
  }, [settings])

  const handleSave = () => {
    onSave(localSettings)
    onClose()
  }

  const handleRestoreDefaults = () => {
    setLocalSettings(DEFAULT_SETTINGS)
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className={components.modal.overlay}
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={cn(
          "fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[520px] max-w-[calc(100vw-32px)] max-h-[calc(100vh-64px)] overflow-y-auto"
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={cn(components.modal.container, "w-full !mx-0")}>
          {/* Header */}
          <div className={cn(components.modal.header, "flex items-center justify-between")}>
            <h2 className={components.modal.title}>Session Settings</h2>
            <button
              type="button"
              onClick={onClose}
              className={components.modal.closeButton}
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Settings Form */}
          <div className={cn(components.modal.content, spacing.stack.xl)}>
            {/* Default Duration */}
            <div>
              <label className={components.input.label}>
                Default Focus Duration (minutes)
              </label>
              <input
                type="number"
                value={localSettings.defaultDuration}
                onChange={(e) => setLocalSettings({
                  ...localSettings,
                  defaultDuration: Math.max(1, Math.min(120, parseInt(e.target.value) || 25))
                })}
                className={components.input.base}
                min="1"
                max="120"
              />
            </div>

            {/* Default Break */}
            <div>
              <label className={components.input.label}>
                Default Break Duration (minutes)
              </label>
              <input
                type="number"
                value={localSettings.defaultBreak}
                onChange={(e) => setLocalSettings({
                  ...localSettings,
                  defaultBreak: Math.max(1, Math.min(30, parseInt(e.target.value) || 5))
                })}
                className={components.input.base}
                min="1"
                max="30"
              />
            </div>

            {/* Cycles Per Session */}
            <div>
              <label className={components.input.label}>
                Number of Cycles Per Session
              </label>
              <input
                type="number"
                value={localSettings.cyclesPerSession}
                onChange={(e) => setLocalSettings({
                  ...localSettings,
                  cyclesPerSession: Math.max(1, Math.min(10, parseInt(e.target.value) || 4))
                })}
                className={components.input.base}
                min="1"
                max="10"
              />
              <p className={components.input.helper}>
                How many focus-break cycles before a longer break
              </p>
            </div>

            {/* Auto-start Options */}
            <div className={spacing.stack.sm}>
              <label className={cn("flex items-center gap-3 cursor-default")}>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={localSettings.autoStartNextSession}
                    onChange={(e) => setLocalSettings({
                      ...localSettings,
                      autoStartNextSession: e.target.checked
                    })}
                    className="peer sr-only"
                  />
                  <div className="w-5 h-5 border-2 border-gray-600 rounded bg-neutral-800/40 hover:border-gray-500 peer-checked:bg-blue-600 peer-checked:border-blue-600 transition-all">
                    {localSettings.autoStartNextSession && (
                      <svg className="w-full h-full text-white" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </div>
                <span className={cn(typography.body.default, colors.text.secondary)}>
                  Auto-start next focus session
                </span>
              </label>

              <label className={cn("flex items-center gap-3 cursor-default")}>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={localSettings.autoStartBreaks}
                    onChange={(e) => setLocalSettings({
                      ...localSettings,
                      autoStartBreaks: e.target.checked
                    })}
                    className="peer sr-only"
                  />
                  <div className="w-5 h-5 border-2 border-gray-600 rounded bg-neutral-800/40 hover:border-gray-500 peer-checked:bg-blue-600 peer-checked:border-blue-600 transition-all">
                    {localSettings.autoStartBreaks && (
                      <svg className="w-full h-full text-white" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </div>
                <span className={cn(typography.body.default, colors.text.secondary)}>
                  Auto-start breaks
                </span>
              </label>
            </div>

            {/* Notification Options */}
            <div>
              <h3 className={cn(typography.subsectionTitle, colors.text.secondary, "mb-3")}>Notifications</h3>
              <div className={spacing.stack.sm}>
                <label className={cn("flex items-center gap-3 cursor-default")}>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={localSettings.playSoundOnComplete}
                      onChange={(e) => setLocalSettings({
                        ...localSettings,
                        playSoundOnComplete: e.target.checked
                      })}
                      className="peer sr-only"
                    />
                    <div className="w-5 h-5 border-2 border-gray-600 rounded bg-neutral-800/40 hover:border-gray-500 peer-checked:bg-blue-600 peer-checked:border-blue-600 transition-all">
                      {localSettings.playSoundOnComplete && (
                        <svg className="w-full h-full text-white" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </div>
                  <span className={cn(typography.body.default, colors.text.secondary)}>
                    Play sound when focus ends
                  </span>
                </label>

                <label className={cn("flex items-center gap-3 cursor-default")}>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={localSettings.desktopNotifications}
                      onChange={(e) => setLocalSettings({
                        ...localSettings,
                        desktopNotifications: e.target.checked
                      })}
                      className="peer sr-only"
                    />
                    <div className="w-5 h-5 border-2 border-gray-600 rounded bg-neutral-800/40 hover:border-gray-500 peer-checked:bg-blue-600 peer-checked:border-blue-600 transition-all">
                      {localSettings.desktopNotifications && (
                        <svg className="w-full h-full text-white" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </div>
                  <span className={cn(typography.body.default, colors.text.secondary)}>
                    Desktop notification on session completion
                  </span>
                </label>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className={components.modal.footer}>
            <button
              type="button"
              onClick={handleRestoreDefaults}
              className={cn(components.button.base, components.button.secondary, "flex-1")}
            >
              Restore Defaults
            </button>
            <button
              type="button"
              onClick={handleSave}
              className={cn(components.button.base, components.button.primary, "flex-1")}
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

export { type PomodoroSettings, DEFAULT_SETTINGS }

