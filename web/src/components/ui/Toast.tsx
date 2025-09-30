import React, { useEffect, useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { toast } from '../../lib/toast'
import { cn } from '../../lib/utils'

interface ToastProps {
  id: string
  title: string
  description?: string
  type: 'success' | 'error' | 'warning' | 'info'
  onDismiss: (id: string) => void
}

const ToastItem = ({ id, title, description, type, onDismiss }: ToastProps) => {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
  }

  const colors = {
    success: 'border-success bg-success/10 text-success',
    error: 'border-error bg-error text-white',
    warning: 'border-warning bg-warning/10 text-warning',
    info: 'border-primary bg-primary/10 text-primary',
  }

  const Icon = icons[type]

  return (
    <div className={cn(
      'flex items-start gap-3 p-4 rounded-lg border shadow-lg max-w-sm',
      colors[type]
    )}>
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
      
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm">{title}</div>
        {description && (
          <div className="text-xs opacity-90 mt-1">{description}</div>
        )}
      </div>
      
      <button
        onClick={() => onDismiss(id)}
        className="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<any[]>([])

  useEffect(() => {
    const unsubscribe = toast.subscribe((state) => {
      setToasts(state.toasts)
    })

    return unsubscribe
  }, [])

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toastItem) => (
        <ToastItem
          key={toastItem.id}
          {...toastItem}
          onDismiss={toast.dismiss}
        />
      ))}
    </div>
  )
}