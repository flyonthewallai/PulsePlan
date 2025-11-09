/**
 * Commands API Client
 * Handles command execution requests to backend
 */

import { apiClient } from './client';
import type { CommandResult, CommandExecuteRequest, Command } from '@/lib/commands/types';

const COMMANDS_BASE = '/api/v1/commands';

export const commandsApi = {
  /**
   * Execute a command
   */
  execute: async (
    command: string,
    parameters: Record<string, any>,
    rawText: string
  ): Promise<CommandResult> => {
    const request: CommandExecuteRequest = {
      command,
      parameters,
      raw_text: rawText,
    };

    const response = await apiClient.post<CommandResult>(
      `${COMMANDS_BASE}/execute`,
      request
    );

    if (response.error) {
      throw new Error(response.error);
    }

    return response.data!;
  },

  /**
   * List all available commands
   */
  list: async (): Promise<Command[]> => {
    const response = await apiClient.get<Command[]>(`${COMMANDS_BASE}/list`);

    if (response.error) {
      throw new Error(response.error);
    }

    return response.data || [];
  },
};

// Legacy export for backward compatibility
export const commandsAPI = {
  execute: commandsApi.execute,
  list: commandsApi.list,
};

