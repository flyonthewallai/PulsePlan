/**
 * CommandBadge Component
 * Visual chip/pill displaying active command
 */

import React from 'react';
import { X } from 'lucide-react';
import { cn } from '../lib/utils';

interface CommandBadgeProps {
  commandName: string;
  onRemove?: () => void;
  className?: string;
}

export function CommandBadge({ commandName, onRemove, className }: CommandBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-3 py-1.5 bg-neutral-800/40 border border-gray-700/30 rounded-lg text-blue-400 font-medium text-sm',
        className
      )}
    >
      /{commandName}
      {onRemove && (
        <button
          onClick={onRemove}
          className="hover:bg-white/10 rounded p-0.5 transition-colors -mr-0.5"
          aria-label="Remove command"
        >
          <X size={14} />
        </button>
      )}
    </span>
  );
}

