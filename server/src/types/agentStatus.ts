export interface AgentStatusUpdate {
  tool: string;
  status: 'active' | 'completed' | 'error' | 'idle';
  userId: string;
  timestamp?: string;
  message?: string;
  metadata?: Record<string, any>;
}

export interface AgentStatusQueueItem extends AgentStatusUpdate {
  id: string;
  timestamp: string;
  retryCount?: number;
}

export interface UserAgentStatus {
  userId: string;
  currentTool?: string;
  status: 'idle' | 'active' | 'error';
  lastUpdate: string;
  toolHistory: Array<{
    tool: string;
    status: string;
    timestamp: string;
    message?: string;
  }>;
}

export type AgentStatusEventType = 'status_update' | 'tool_change' | 'agent_idle' | 'agent_error'; 