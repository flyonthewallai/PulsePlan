import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { todosService, type Todo, type CreateTodoData, type UpdateTodoData } from '@/services/tasks'
import { addPendingTodoMutation, removePendingTodoMutation, pendingTodoMutations } from './useTodoUpdates'
import { TODO_CACHE_KEYS } from '@/hooks/shared/cacheKeys'

export const useTodos = (filters?: {
  completed?: boolean;
  priority?: Todo['priority'];
  status?: Todo['status'];
  tags?: string[];
}) => {
  // Always use the same cache key to avoid duplicate cache entries
  const queryKey = TODO_CACHE_KEYS.TODOS
  
  return useQuery({
    queryKey,
    queryFn: () => todosService.getTodos(filters || {}),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,  // 10 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    retry: 2,
  })
}

export const useCreateTodo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (newTodo: CreateTodoData) => todosService.createTodo(newTodo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
    },
  })
}

export const useUpdateTodo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, updates }: { id: string, updates: UpdateTodoData }) => 
      todosService.updateTodo(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
    },
  })
}

export const useDeleteTodo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => todosService.deleteTodo(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
    },
  })
}

export const useToggleTodo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (todoId: string) => {
      // Find the todo in cached data - need to check all todo query variations
      let todo: Todo | undefined

      // Get all queries that match the todos cache key pattern
      const queryCache = queryClient.getQueryCache()
      const todoQueries = queryCache.findAll({ queryKey: TODO_CACHE_KEYS.TODOS })

      // Search through all cached todo queries to find the todo
      for (const query of todoQueries) {
        const data = query.state.data as { data: Todo[] | null; error: string | null } | undefined
        if (data?.data) {
          todo = data.data.find(t => t.id === todoId)
          if (todo) break
        }
      }

      if (!todo) {
        throw new Error('Todo not found')
      }

      const newCompleted = !todo.completed
      return todosService.toggleTodoCompletion(todoId, newCompleted)
    },
    onMutate: async (todoId) => {
      // Mark this todo as having a pending mutation to prevent real-time updates
      addPendingTodoMutation(todoId)
      
      await queryClient.cancelQueries({ queryKey: TODO_CACHE_KEYS.TODOS })

      // Store previous data from all todo queries for rollback
      const queryCache = queryClient.getQueryCache()
      const todoQueries = queryCache.findAll({ queryKey: TODO_CACHE_KEYS.TODOS })
      const previousData = new Map()

      // Update all cached todo queries
      for (const query of todoQueries) {
        const queryKey = query.queryKey
        const previousTodos = queryClient.getQueryData(queryKey)
        previousData.set(queryKey, previousTodos)
        
        queryClient.setQueryData<{ data: Todo[] | null; error: string | null }>(queryKey, (old) => {
          if (!old?.data) return old
          return {
            ...old,
            data: old.data.map(todo =>
              todo.id === todoId
                ? { ...todo, completed: !todo.completed }
                : todo
            )
          }
        })
      }

      return { previousData }
    },
    onError: (err, todoId, context) => {
      console.error('Failed to toggle todo:', err)
      // Remove pending mutation tracking on error
      removePendingTodoMutation(todoId)
      
      if (context?.previousData) {
        // Restore all previous query data on error
        for (const [queryKey, previousTodos] of context.previousData) {
          queryClient.setQueryData(queryKey, previousTodos)
        }
      }
    },
    onSettled: (data, error, todoId) => {
      // Remove pending mutation tracking when mutation completes
      removePendingTodoMutation(todoId)
      
      // Force update the cache with the actual API response
      if (data?.data && !error) {
        queryClient.setQueryData(TODO_CACHE_KEYS.TODOS, (old: any) => {
          if (!old?.data) return old
          return {
            ...old,
            data: old.data.map((todo: Todo) =>
              todo.id === todoId ? data.data : todo
            )
          }
        })
      }
      
      // Invalidate to refetch fresh data
      queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
    }
  })
}
