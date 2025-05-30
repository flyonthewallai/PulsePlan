// Mock task data for the app
export type Task = {
  id: string;
  title: string;
  subject: string;
  dueDate: string;
  dueTime: string;
  priority: 'high' | 'medium' | 'low';
  completed: boolean;
  description?: string;
  timeEstimate?: number; // in minutes
};

// Mock tasks for today view
export const mockTasks: Task[] = [
  {
    id: '1',
    title: 'Complete Calculus Assignment',
    subject: 'Math',
    dueDate: '2025-06-12',
    dueTime: '14:00',
    priority: 'high',
    completed: false,
    description: 'Pages 45-50, problems 1-15',
    timeEstimate: 60,
  },
  {
    id: '2',
    title: 'Study for Physics Quiz',
    subject: 'Science',
    dueDate: '2025-06-12',
    dueTime: '16:00',
    priority: 'medium',
    completed: false,
    description: 'Review chapters 7-9',
    timeEstimate: 90,
  },
  {
    id: '3',
    title: 'Read Literature Assignment',
    subject: 'English',
    dueDate: '2025-06-12',
    dueTime: '18:00',
    priority: 'low',
    completed: true,
    description: 'Read chapters 4-5 of The Great Gatsby',
    timeEstimate: 45,
  },
  {
    id: '4',
    title: 'Group Project Meeting',
    subject: 'History',
    dueDate: '2025-06-12',
    dueTime: '19:30',
    priority: 'high',
    completed: false,
    description: 'Discuss research findings',
    timeEstimate: 60,
  },
  {
    id: '5',
    title: 'Submit Canvas Discussion Post',
    subject: 'Psychology',
    dueDate: '2025-06-12',
    dueTime: '23:59',
    priority: 'medium',
    completed: false,
    description: 'Post response to weekly discussion',
    timeEstimate: 30,
  },
];

// Mock progress data
export const mockProgress = {
  tasksCompleted: 12,
  totalTasks: 20,
  focusHours: 4.5,
  streak: 7,
  weeklyGoal: 30,
};

// Mock week view data
export const mockWeekData = {
  monday: [
    {
      id: 'w1',
      title: 'Math Study Session',
      time: '09:00-10:30',
      subject: 'Math',
      priority: 'high',
    },
    {
      id: 'w2',
      title: 'English Essay',
      time: '14:00-15:30',
      subject: 'English',
      priority: 'medium',
    },
  ],
  tuesday: [
    {
      id: 'w3',
      title: 'Physics Lab',
      time: '10:00-12:00',
      subject: 'Science',
      priority: 'high',
    },
  ],
  wednesday: [
    {
      id: 'w4',
      title: 'History Research',
      time: '13:00-15:00',
      subject: 'History',
      priority: 'medium',
    },
  ],
  thursday: [
    {
      id: 'w5',
      title: 'Chemistry Review',
      time: '16:00-17:00',
      subject: 'Science',
      priority: 'low',
    },
  ],
  friday: [
    {
      id: 'w6',
      title: 'Literature Analysis',
      time: '11:00-12:30',
      subject: 'English',
      priority: 'medium',
    },
  ],
  saturday: [],
  sunday: [
    {
      id: 'w7',
      title: 'Weekly Review',
      time: '19:00-20:00',
      subject: 'General',
      priority: 'low',
    },
  ],
};

// Convert week data to array format for week.tsx (Sun=0, Mon=1, etc.)
export const mockTasksByDay: Task[][] = [
  // Sunday (0)
  [
    {
      id: 'w7',
      title: 'Weekly Review',
      subject: 'General',
      dueDate: '2025-06-15',
      dueTime: '19:00',
      priority: 'low',
      completed: false,
      timeEstimate: 60,
    },
  ],
  // Monday (1)
  [
    {
      id: 'w1',
      title: 'Math Study Session',
      subject: 'Math',
      dueDate: '2025-06-16',
      dueTime: '09:00',
      priority: 'high',
      completed: false,
      timeEstimate: 90,
    },
    {
      id: 'w2',
      title: 'English Essay',
      subject: 'English',
      dueDate: '2025-06-16',
      dueTime: '14:00',
      priority: 'medium',
      completed: false,
      timeEstimate: 90,
    },
  ],
  // Tuesday (2)
  [
    {
      id: 'w3',
      title: 'Physics Lab',
      subject: 'Science',
      dueDate: '2025-06-17',
      dueTime: '10:00',
      priority: 'high',
      completed: false,
      timeEstimate: 120,
    },
  ],
  // Wednesday (3)
  [
    {
      id: 'w4',
      title: 'History Research',
      subject: 'History',
      dueDate: '2025-06-18',
      dueTime: '13:00',
      priority: 'medium',
      completed: false,
      timeEstimate: 120,
    },
  ],
  // Thursday (4)
  [
    {
      id: 'w5',
      title: 'Chemistry Review',
      subject: 'Science',
      dueDate: '2025-06-19',
      dueTime: '16:00',
      priority: 'low',
      completed: false,
      timeEstimate: 60,
    },
  ],
  // Friday (5)
  [
    {
      id: 'w6',
      title: 'Literature Analysis',
      subject: 'English',
      dueDate: '2025-06-20',
      dueTime: '11:00',
      priority: 'medium',
      completed: false,
      timeEstimate: 90,
    },
  ],
  // Saturday (6)
  [],
]; 