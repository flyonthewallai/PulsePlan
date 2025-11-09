/**
 * Command Parser Hook
 * Detects commands, extracts parameters, and manages command state
 */

import { useState, useEffect, useMemo } from 'react';
import type { Command, ParsedCommand } from '@/lib/commands/types';
import { getCommand, matchCommands, getAllCommands } from '@/lib/commands/definitions';
import { extractParameters } from '@/lib/commands/extractors';

export interface UseCommandParserReturn {
  isCommandMode: boolean;
  suggestions: Command[];
  selectedCommand: Command | null;
  parsedCommand: ParsedCommand | null;
  selectCommand: (command: Command) => void;
  clearCommand: () => void;
  parseInput: (input: string) => ParsedCommand | null;
}

export function useCommandParser(inputValue: string): UseCommandParserReturn {
  const [selectedCommand, setSelectedCommand] = useState<Command | null>(null);
  const [parsedCommand, setParsedCommand] = useState<ParsedCommand | null>(null);

  // Detect if we're in command mode (starts with /)
  const isCommandMode = useMemo(() => {
    return inputValue.trim().startsWith('/');
  }, [inputValue]);

  // Get command suggestions based on current input
  const suggestions = useMemo(() => {
    if (!isCommandMode) return [];
    
    // Extract command part (first word after /)
    const commandPart = inputValue.trim().slice(1).split(/\s+/)[0];
    
    // If no command text yet, show all commands
    if (!commandPart) return getAllCommands();
    
    // Otherwise fuzzy match
    return matchCommands(commandPart);
  }, [inputValue, isCommandMode]);

  // Parse the input when it changes
  useEffect(() => {
    if (!isCommandMode) {
      setParsedCommand(null);
      return;
    }

    const parsed = parseInput(inputValue);
    setParsedCommand(parsed);
  }, [inputValue, isCommandMode]);

  /**
   * Parse input text into a ParsedCommand
   */
  const parseInput = (input: string): ParsedCommand | null => {
    if (!input.trim().startsWith('/')) return null;

    // Extract command name (first word after /)
    const parts = input.trim().slice(1).split(/\s+/);
    const commandName = parts[0];
    const remainingText = parts.slice(1).join(' ');

    // Find command
    const command = getCommand(commandName);
    if (!command) return null;

    // Extract parameters from remaining text
    const parameters = extractParameters(remainingText, command.id);

    // Check for missing required parameters
    const missingRequired = command.parameterSchema
      .filter(param => param.required && !parameters[param.name])
      .map(param => param.name);

    // Calculate confidence (higher if all required params present)
    const confidence = missingRequired.length === 0 ? 0.95 : 0.6;

    return {
      command,
      parameters,
      confidence,
      missingRequired,
      rawText: input,
    };
  };

  /**
   * Select a command from suggestions
   */
  const selectCommand = (command: Command) => {
    setSelectedCommand(command);
  };

  /**
   * Clear the selected command
   */
  const clearCommand = () => {
    setSelectedCommand(null);
    setParsedCommand(null);
  };

  return {
    isCommandMode,
    suggestions,
    selectedCommand,
    parsedCommand,
    selectCommand,
    clearCommand,
    parseInput,
  };
}

