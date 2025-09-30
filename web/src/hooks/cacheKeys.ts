// Cache keys for consistent invalidation across hooks
export const TASK_CACHE_KEYS = {
  TASKS: ['tasks'],
  TASKS_BY_DATE: (date: string) => ['tasks', 'date', date],
  TASKS_BY_STATUS: (status: string) => ['tasks', 'status', status],
  TASKS_BY_COURSE: (courseId: string) => ['tasks', 'course', courseId],
  TASK_DETAILS: (taskId: string) => ['tasks', 'details', taskId],
}

export const TODO_CACHE_KEYS = {
  TODOS: ['todos'],
  TODOS_BY_DATE: (date: string) => ['todos', 'date', date],
  TODOS_BY_STATUS: (status: string) => ['todos', 'status', status],
  TODO_DETAILS: (todoId: string) => ['todos', 'details', todoId],
}

export const OAUTH_CACHE_KEYS = {
  CONNECTIONS: ['oauth-connections'],
  CONNECTION_STATUS: (provider: string) => ['oauth-connections', provider],
}




