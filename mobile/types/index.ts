export interface AgentResponse {
  success: boolean;
  message?: string;
  data?: any;
  error?: string;
  conversationId?: string;
  timestamp?: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  dueDate: string;
  priority: 'high' | 'medium' | 'low';
  status: 'todo' | 'in_progress' | 'completed';
  estimatedDuration: number;
  scheduledHour?: number;
  tags?: string[];
  scheduling_rationale?: string;
  createdAt: string;
  updatedAt: string;
}

export type CreateTaskData = Omit<Task, 'id' | 'createdAt' | 'updatedAt'>;

export interface AgentMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}