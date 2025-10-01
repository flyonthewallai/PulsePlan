import React, { useEffect, useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Info, X, Loader2 } from 'lucide-react'
import { toast } from '../../lib/toast'
import { cn } from '../../lib/utils'

interface ToastProps {
  id: string
  title: string
  description?: string
  type: 'success' | 'error' | 'warning' | 'info' | 'loading'
  onDismiss: (id: string) => void
}

const ToastItem = ({ id, title, description, type, onDismiss }: ToastProps) => {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
    loading: Loader2,
  }

  // Solid backgrounds, white text to match sync banners
  const colors = {
    success: 'bg-green-600 border-green-500 text-white',
    error: 'bg-red-600 border-red-500 text-white',
    warning: 'bg-yellow-600 border-yellow-500 text-white',
    info: 'bg-blue-600 border-blue-500 text-white',
    loading: 'bg-blue-600 border-blue-500 text-white',
  }

  const Icon = icons[type]

  return (
    <div className={cn(
      'flex items-start gap-3 p-4 rounded-lg border shadow-lg max-w-sm',
      colors[type]
    )}>
      <Icon className={cn('w-5 h-5 flex-shrink-0 mt-0.5', type === 'loading' && 'animate-spin')} />
      
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