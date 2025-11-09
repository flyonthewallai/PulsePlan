/**
 * Command System Type Definitions
 * Defines interfaces for the deterministic command shortcut system
 */

export type ParameterType = 'string' | 'datetime' | 'enum' | 'string[]' | 'number' | 'boolean';

export interface ParameterDefinition {
  name: string;
  type: ParameterType;
  required: boolean;
  description?: string;
  values?: string[]; // For enum types
  default?: any;
}

export interface Command {
  id: string;
  name: string;
  label: string;
  description: string;
  icon: string; // Lucide icon name
  aliases: string[];
  parameterSchema: ParameterDefinition[];
  examples?: string[];
}

export interface ParsedCommand {
  command: Command;
  parameters: Record<string, any>;
  confidence: number;
  missingRequired: string[];
  rawText: string;
}

export interface CommandResult {
  success: boolean;
  command: string;
  result?: any;
  immediate_response: string;
  error?: string;
  requires_clarification?: boolean;
  clarification_prompt?: string;
}

export interface CommandExecuteRequest {
  command: string;
  parameters: Record<string, any>;
  raw_text: string;
}

export interface ExtractedParameter {
  name: string;
  value: any;
  confidence: number;
  rawText: string;
  startIndex: number;
  endIndex: number;
}