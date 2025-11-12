import React from 'react'
import { Check, X, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface IntegrationStatusBadgeProps {
  status: 'connected' | 'disconnected' | 'coming-soon'
  className?: string
}

export function IntegrationStatusBadge({ status, className }: IntegrationStatusBadgeProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Check,
          text: 'Connected',
          className: 'bg-green-900/20 text-green-400 border-green-700/50'
        }
      case 'disconnected':
        return {
          icon: X,
          text: 'Disconnected',
          className: 'bg-red-900/20 text-red-400 border-red-700/50'
        }
      case 'coming-soon':
        return {
          icon: Clock,
          text: 'Coming Soon',
          className: 'bg-yellow-900/20 text-yellow-400 border-yellow-700/50'
        }
    }
  }

  const config = getStatusConfig()
  const Icon = config.icon

  return (
    <div className={cn(
      'inline-flex items-center gap-1.5 px-2 py-1 rounded-full border text-xs font-medium',
      config.className,
      className
    )}>
      <Icon className="w-3 h-3" />
      {config.text}
    </div>
  )
}