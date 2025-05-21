export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string;
  subject: string;
  due_date: string;
  estimated_minutes?: number;
  status: 'pending' | 'in_progress' | 'completed';
  priority: 'low' | 'medium' | 'high';
  created_at: string;
  updated_at: string;
} 