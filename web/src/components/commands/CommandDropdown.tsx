/**
 * CommandDropdown Component
 * Shows command suggestions with keyboard navigation
 */

import React, { useEffect, useRef } from 'react';
import * as Icons from 'lucide-react';
import type { Command } from '@/lib/commands/types';
import { cn } from '../../lib/utils';

interface CommandDropdownProps {
  commands: Command[];
  selectedIndex: number;
  onSelect: (command: Command) => void;
  onClose: () => void;
  position?: 'above' | 'below';
}

export function CommandDropdown({
  commands,
  selectedIndex,
  onSelect,
  onClose,
  position = 'above',
}: CommandDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && selectedIndex < itemRefs.current.length) {
      itemRefs.current[selectedIndex]?.scrollIntoView({
        block: 'nearest',
        behavior: 'smooth',
      });
    }
  }, [selectedIndex]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  if (commands.length === 0) return null;

  // Show top 5 by default, keep it compact
  const visibleCommands = commands.slice(0, 5);

  return (
    <div
      ref={dropdownRef}
      className={cn(
        'absolute left-0 z-50 bg-[#1a1a1a] border border-white/10 rounded-lg shadow-lg overflow-hidden mb-1',
        position === 'above' ? 'bottom-full' : 'top-full mt-1'
      )}
      style={{ maxHeight: '140px', width: '240px' }}
    >
      <div className="overflow-y-auto max-h-[140px]">
        {visibleCommands.map((command, index) => {
          const IconComponent = (Icons as any)[command.icon] || Icons.HelpCircle;
          const isSelected = index === selectedIndex;

          return (
            <button
              key={command.id}
              ref={el => itemRefs.current[index] = el}
              onClick={() => onSelect(command)}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-1.5 text-left transition-colors text-sm',
                isSelected
                  ? 'bg-white/5 text-[#E5E5E5]'
                  : 'text-[#E5E5E5] hover:bg-white/5'
              )}
            >
              <IconComponent
                size={16}
                className={cn(
                  'flex-shrink-0 text-gray-400',
                  isSelected && 'text-white'
                )}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium">
                    /{command.name}
                  </span>
                  {command.aliases.length > 0 && (
                    <span className="text-xs text-gray-500">
                      (/{command.aliases[0]})
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400 mt-0.5 truncate">
                  {command.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

