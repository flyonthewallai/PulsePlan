import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from '../contexts/WebSocketContext'
import { supabase } from '../lib/supabase'
import { TODO_CACHE_KEYS } from './cacheKeys'

// Track pending todo mutations to prevent race conditions
export const pendingTodoMutations = new Set<string>()

export const addPendingTodoMutation = (todoId: string) => {
  pendingTodoMutations.add(todoId)
}

export const removePendingTodoMutation = (todoId: string) => {
  pendingTodoMutations.delete(todoId)
}

export const useTodoUpdates = () => {
  const queryClient = useQueryClient()
  const { socket, isConnected } = useWebSocket()
  
  useEffect(() => {
    // Set up Supabase real-time subscription for todos
    
    const setupSubscription = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        return
      }
      
      const channel = supabase
        .channel('todos-changes')
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'todos',
            filter: `user_id=eq.${user.id}`
          },
          (payload) => {
            // Check if this todo has a pending mutation to avoid race conditions
            const newTodo = payload.new as any
            if (newTodo?.id && typeof newTodo.id === 'string' && pendingTodoMutations.has(newTodo.id)) {
              return
            }
            
            queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
          }
        )
        .subscribe()

      return channel
    }
    
    let channel: any = null
    setupSubscription().then((ch) => {
      channel = ch
    })

    return () => {
      if (channel) {
        supabase.removeChannel(channel)
      }
    }
  }, [queryClient])
  
  useEffect(() => {
    if (!socket || !isConnected) {
      return
    }
    
    // Listen for todo creation events
    const handleTodoCreated = (data: any) => {
      console.log('📝 Todo created via WebSocket:', data.data?.title || 'Unknown')
      
      // Extract todo from various possible data structures
      let todo = null
      if (data.todo) {
        todo = data.todo
      } else if (data.data?.todo) {
        todo = data.data.todo
      } else if (data.data?.created_item?.todo) {
        todo = data.data.created_item.todo
      } else if (data.data?.created_item) {
        todo = data.data.created_item
      } else if (data.data && data.data.id) {
        // Direct todo data in data.data (agent-created todos)
        todo = data.data
      }
      
      if (todo && todo.type === 'todo') {
        queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        queryClient.refetchQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
      }
    }
    
    // Listen for todo update events
    const handleTodoUpdated = (data: any) => {
      let todo = null
      if (data.todo) {
        todo = data.todo
      } else if (data.data?.todo) {
        todo = data.data.todo
      } else if (data.data?.updated_item?.todo) {
        todo = data.data.updated_item.todo
      } else if (data.data?.updated_item) {
        todo = data.data.updated_item
      } else if (data.data && data.data.id) {
        // Direct todo data in data.data (agent-updated todos)
        todo = data.data
      }
      
      if (todo && todo.type === 'todo') {
        console.log('🔄 Todo updated via WebSocket:', todo.title, 'ID:', todo.id)
        console.log('🔍 Pending mutations:', Array.from(pendingTodoMutations))
        console.log('🔍 Has pending mutation:', pendingTodoMutations.has(todo.id))
        
        // Check if this todo has a pending mutation to avoid race conditions
        if (pendingTodoMutations.has(todo.id)) {
          console.log('⏭️ Skipping WebSocket update for todo with pending mutation:', todo.id)
          return
        }
        
        console.log('✅ Processing WebSocket update for todo:', todo.id)
        // Invalidate and immediately refetch to ensure UI updates
        queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        queryClient.refetchQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
      }
    }
    
    // Listen for todo deletion events
    const handleTodoDeleted = (data: any) => {
      let todo = null
      if (data.todo) {
        todo = data.todo
      } else if (data.data?.todo) {
        todo = data.data.todo
      } else if (data.data?.deleted_item?.todo) {
        todo = data.data.deleted_item.todo
      } else if (data.data?.deleted_item) {
        todo = data.data.deleted_item
      } else if (data.data && data.data.id) {
        // Direct todo data in data.data (agent-deleted todos)
        todo = data.data
      }
      
      if (todo && todo.type === 'todo') {
        // Invalidate and immediately refetch to ensure UI updates
        queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        queryClient.refetchQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
      }
    }
    
    // Listen for workflow completion that might affect todos
    const handleWorkflowCompletion = (data: any) => {
      // Check if workflow completion includes todo data
      if (data.result?.data?.todo || data.result?.todo) {
        // Invalidate and immediately refetch to ensure UI updates
        queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        queryClient.refetchQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
      }
    }
    
    // Register event listeners
    socket.on('task_created', handleTodoCreated)
    socket.on('task_updated', handleTodoUpdated)
    socket.on('task_deleted', handleTodoDeleted)
    socket.on('workflow_completion', handleWorkflowCompletion)
    
    // Cleanup function
    return () => {
      socket.off('task_created', handleTodoCreated)
      socket.off('task_updated', handleTodoUpdated)
      socket.off('task_deleted', handleTodoDeleted)
      socket.off('workflow_completion', handleWorkflowCompletion)
    }
  }, [socket, isConnected, queryClient])
}
