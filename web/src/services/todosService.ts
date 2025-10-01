import { supabase } from '../lib/supabase'

export interface Todo {
  id: string
  user_id: string
  title: string
  description?: string
  notes?: string
  completed: boolean
  priority: 'low' | 'medium' | 'high'
  due_date?: string
  estimated_minutes?: number
  actual_minutes?: number
  reminder_minutes?: number[]
  tags: string[]
  created_at: string
  completed_at?: string
  updated_at: string
}

export interface CreateTodoData {
  title: string
  description?: string
  notes?: string
  priority?: 'low' | 'medium' | 'high'
  due_date?: string
  estimated_minutes?: number
  reminder_minutes?: number[]
  tags?: string[]
}

export interface UpdateTodoData {
  title?: string
  description?: string
  notes?: string
  completed?: boolean
  priority?: 'low' | 'medium' | 'high'
  due_date?: string
  estimated_minutes?: number
  actual_minutes?: number
  reminder_minutes?: number[]
  tags?: string[]
}

export interface TodoFilters {
  completed?: boolean
  priority?: 'low' | 'medium' | 'high'
  tags?: string[]
}

class TodosService {
  async getTodos(filters: TodoFilters = {}): Promise<{ data: Todo[] | null; error: string | null }> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        return { data: null, error: 'User not authenticated' }
      }

      let query = supabase
        .from('todos')
        .select('*')
        .eq('user_id', user.id)

      // Apply filters
      if (filters.completed !== undefined) {
        query = query.eq('completed', filters.completed)
      }
      if (filters.priority) {
        query = query.eq('priority', filters.priority)
      }

      const { data, error } = await query
        .order('created_at', { ascending: false })

      if (error) {
        return { data: null, error: error.message }
      }

      // Apply tag filtering client-side since Supabase doesn't handle array contains easily
      let filteredData = data || []
      if (filters.tags && filters.tags.length > 0) {
        filteredData = filteredData.filter((todo: Todo) =>
          filters.tags!.some(tag => todo.tags?.includes(tag))
        )
      }

      return { data: filteredData, error: null }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  async createTodo(todoData: CreateTodoData): Promise<{ data: Todo | null; error: string | null }> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        return { data: null, error: 'User not authenticated' }
      }

      const { data, error } = await supabase
        .from('todos')
        .insert({
          user_id: user.id,
          title: todoData.title,
          description: todoData.description,
          priority: todoData.priority || 'medium',
          due_date: todoData.due_date,
          tags: todoData.tags || [],
        })
        .select()
        .single()

      if (error) {
        console.error('Error creating todo:', error)
        return { data: null, error: error.message }
      }

      return { data, error: null }
    } catch (error) {
      console.error('Error in createTodo:', error)
      return { data: null, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  async updateTodo(id: string, updates: UpdateTodoData): Promise<{ data: Todo | null; error: string | null }> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        return { data: null, error: 'User not authenticated' }
      }

      const updateData: any = { ...updates }

      // If marking as completed, set completed_at timestamp
      if (updates.completed === true) {
        updateData.completed_at = new Date().toISOString()
      } else if (updates.completed === false) {
        updateData.completed_at = null
      }

      const { data, error } = await supabase
        .from('todos')
        .update(updateData)
        .eq('id', id)
        .eq('user_id', user.id)
        .select()
        .single()

      if (error) {
        console.error('Error updating todo:', error)
        return { data: null, error: error.message }
      }

      return { data, error: null }
    } catch (error) {
      console.error('Error in updateTodo:', error)
      return { data: null, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  async deleteTodo(id: string): Promise<{ error: string | null }> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        return { error: 'User not authenticated' }
      }

      const { error } = await supabase
        .from('todos')
        .delete()
        .eq('id', id)
        .eq('user_id', user.id)

      if (error) {
        console.error('Error deleting todo:', error)
        return { error: error.message }
      }

      return { error: null }
    } catch (error) {
      console.error('Error in deleteTodo:', error)
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  async toggleTodoCompletion(id: string, completed: boolean): Promise<{ data: Todo | null; error: string | null }> {
    return this.updateTodo(id, { completed })
  }
}

export const todosService = new TodosService()
