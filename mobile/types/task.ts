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