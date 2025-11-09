import React from 'react'
import { CheckCircle, XCircle, Info, AlertTriangle } from 'lucide-react'
import { cn } from '../../lib/utils'

type Variant = 'success' | 'error' | 'info' | 'warning'

interface InlineAlertProps {
  variant: Variant
  title: string
  message?: string
  className?: string
}

export function InlineAlert({ variant, title, message, className }: InlineAlertProps) {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    info: Info,
    warning: AlertTriangle,
  }
  const Icon = icons[variant]

  const styles = {
    success: 'bg-green-600 border-green-500 text-white',
    error: 'bg-red-700 border-red-600 text-white',
    info: 'bg-blue-600 border-blue-500 text-white',
    warning: 'bg-yellow-600 border-yellow-500 text-white',
  }[variant]

  return (
    <div className={cn('p-4 border rounded-xl flex items-center gap-3', styles, className)}>
      <Icon className="w-5 h-5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium">{title}</p>
        {message && <p className="text-white/90 text-xs">{message}</p>}
      </div>
    </div>
  )
}




