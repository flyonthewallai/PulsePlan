import { cn } from '../../lib/utils'

interface ToggleSwitchProps {
  enabled: boolean
  onToggle: () => void
  label: string
  description?: string
  icon?: React.ReactNode
}

export function ToggleSwitch({ enabled, onToggle, label, description, icon }: ToggleSwitchProps) {
  return (
    <div className="p-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {icon}
        <div>
          <div className="text-white text-sm font-medium">{label}</div>
          {description && <div className="text-xs text-gray-400">{description}</div>}
        </div>
      </div>
      <button
        onClick={onToggle}
        className={cn(
          "w-10 h-5 rounded-full transition-colors",
          enabled ? "bg-blue-500" : "bg-gray-600"
        )}
      >
        <div
          className={cn(
            "w-4 h-4 bg-white rounded-full transition-transform",
            enabled ? "translate-x-5" : "translate-x-0.5"
          )}
        />
      </button>
    </div>
  )
}

