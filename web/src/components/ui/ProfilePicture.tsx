import React from 'react'
import { cn } from '../../lib/utils'

interface ProfilePictureProps {
  name?: string
  email?: string
  imageUrl?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function ProfilePicture({ 
  name, 
  email, 
  imageUrl, 
  size = 'md',
  className 
}: ProfilePictureProps) {
  // Generate initials from name or email
  const getInitials = () => {
    if (name) {
      return name
        .split(' ')
        .map(word => word.charAt(0))
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }
    
    if (email) {
      return email.charAt(0).toUpperCase()
    }
    
    return 'U'
  }

  // Size classes
  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-12 h-12 text-base'
  }

  const initials = getInitials()

  return (
    <div className={cn(
      'rounded-lg bg-neutral-700 flex items-center justify-center text-white font-semibold flex-shrink-0',
      sizeClasses[size],
      className
    )}>
      {imageUrl ? (
        <img 
          src={imageUrl} 
          alt={name || 'Profile'} 
          className="w-full h-full rounded-lg object-cover"
        />
      ) : (
        <span>{initials}</span>
      )}
    </div>
  )
}

