/**
 * CommandInput Component
 * Unified input with command detection, dropdown, and parameter highlighting
 */

import React, { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { ArrowUp, Mic } from 'lucide-react';
import { useCommandParser } from '@/hooks/ui';
import { CommandDropdown } from './CommandDropdown';
import { CommandBadge } from './CommandBadge';
import type { Command } from '@/lib/commands/types';
import { cn } from '../../lib/utils';
import { components } from '../../lib/design-tokens';

interface CommandInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  disabled?: boolean;
  showCommands?: boolean;
  className?: string;
  textSize?: 'sm' | 'base';
}

// Command-specific placeholder text
const commandPlaceholders: Record<string, string> = {
  todo: 'Type your to-do title',
  schedule: 'Event title and time',
  reschedule: 'Task name and new time',
  focus: 'What to focus on',
  briefing: '',
  help: ''
};

export function CommandInput({
  value,
  onChange,
  onSubmit,
  placeholder = 'How can I help you today?',
  disabled = false,
  showCommands = true,
  className,
  textSize = 'base',
}: CommandInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(0);

  const {
    isCommandMode,
    suggestions,
    selectedCommand,
    selectCommand,
    clearCommand,
  } = useCommandParser(value);

  // Get dynamic placeholder based on selected command
  const dynamicPlaceholder = selectedCommand && commandPlaceholders[selectedCommand.id] 
    ? commandPlaceholders[selectedCommand.id] 
    : placeholder;

  // Show dropdown when in command mode with suggestions
  useEffect(() => {
    if (isCommandMode && suggestions.length > 0 && !selectedCommand) {
      setShowDropdown(true);
      setSelectedSuggestionIndex(0);
    } else {
      setShowDropdown(false);
    }
  }, [isCommandMode, suggestions.length, selectedCommand]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 128) + 'px';
    }
  }, [value]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (showDropdown) {
      // Navigate dropdown with arrow keys
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedSuggestionIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedSuggestionIndex(prev => (prev > 0 ? prev - 1 : prev));
        return;
      }
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSelectCommand(suggestions[selectedSuggestionIndex]);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setShowDropdown(false);
        return;
      }
    } else {
      // Normal submit on Enter
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        onSubmit();
        return;
      }
    }

    // Handle backspace on command badge
    if (e.key === 'Backspace' && selectedCommand && value.trim() === `/${selectedCommand.name}`) {
      e.preventDefault();
      clearCommand();
      onChange('');
    }
  };

  const handleSelectCommand = (command: Command) => {
    selectCommand(command);
    setShowDropdown(false);
    
    // Replace input with command name and space
    onChange(`/${command.name} `);
    
    // Focus textarea
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;

    // If a command is selected, prepend it to the new value
    if (selectedCommand) {
      onChange(`/${selectedCommand.name} ${newValue}`);
    } else {
      onChange(newValue);
    }

    // Clear selected command if user manually types a different command
    if (newValue.trim().startsWith('/') && !newValue.startsWith(`/${selectedCommand?.name}`)) {
      clearCommand();
    }
  };

  return (
    <div className={cn('relative w-full', className)}>
      {/* Input Container */}
      <div className="bg-neutral-800/40 border border-gray-700/50 rounded-2xl p-3">
        <div className="flex items-center gap-2 relative">
          {/* Command Dropdown - positioned right above the textarea */}
          {showDropdown && showCommands && (
            <CommandDropdown
              commands={suggestions}
              selectedIndex={selectedSuggestionIndex}
              onSelect={handleSelectCommand}
              onClose={() => setShowDropdown(false)}
              position="above"
            />
          )}
          {/* Show command badge if command selected */}
          {selectedCommand && showCommands && (
            <CommandBadge
              commandName={selectedCommand.name}
              onRemove={() => {
                clearCommand();
                onChange('');
              }}
            />
          )}

          <textarea
            ref={textareaRef}
            placeholder={dynamicPlaceholder}
            value={selectedCommand ? value.replace(`/${selectedCommand.name} `, '').trimStart() : value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            className={cn(
              "flex-1 bg-transparent text-white placeholder-gray-400 focus:outline-none min-h-[42px] max-h-32 resize-none",
              textSize === 'sm' ? 'text-sm' : 'text-base',
              selectedCommand ? "leading-6 py-2" : ""
            )}
            rows={1}
            style={{
              height: 'auto',
              minHeight: '42px',
              maxHeight: '128px',
            }}
          />

          <button
            onClick={onSubmit}
            disabled={value.trim() === '' || disabled}
            className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center transition-all bg-white hover:bg-gray-100',
              value.trim() === '' || disabled
                ? 'opacity-30 cursor-not-allowed'
                : 'opacity-100'
            )}
            aria-label="Send"
          >
            <ArrowUp size={16} className="text-black" />
          </button>
        </div>

        {/* Helper icons below the text when no command is active */}
        {!selectedCommand && (
          <div className="mt-0.1 flex items-center gap-1 text-gray-500/70">
            {/* Small paperclip button */}
            <button
              type="button"
              aria-label="Attach"
              className={components.iconButton.small}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-gray-500">
                <path d="M21.44 11.05L12.5 20c-2.34 2.34-6.14 2.34-8.49 0-2.34-2.34-2.34-6.14 0-8.49l8.49-8.49c1.56-1.56 4.09-1.56 5.66 0 1.56 1.56 1.56 4.09 0 5.66l-8.49 8.49c-.78.78-2.05.78-2.83 0-.78-.78-.78-2.05 0-2.83l7.78-7.78" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
            {/* Microphone button */}
            <button
              type="button"
              aria-label="Voice input"
              className={components.iconButton.small}
            >
              <Mic size={14} className="text-gray-500" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

