import { useMemo } from 'react'
import type { Todo } from '../../../services/tasks'

type TodoTimeFilter = 'all' | 'due_soon'

interface UseTodoFilteringProps {
  todos: Todo[]
  timeFilter: TodoTimeFilter
  searchQuery: string
  getEffectiveCompletedState: (todo: Todo) => boolean
}

export function useTodoFiltering({
  todos,
  timeFilter,
  searchQuery,
  getEffectiveCompletedState,
}: UseTodoFilteringProps) {
  const { today, endOfWeek } = useMemo(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const endOfWeek = new Date(today)
    endOfWeek.setDate(endOfWeek.getDate() + 7)
    return { today, endOfWeek }
  }, [new Date().toDateString()])

  const { allTodosFiltered, undatedTodos } = useMemo(() => {
    let filtered = todos

    // Apply time filter
    if (timeFilter === 'all') {
      filtered = todos
    } else if (timeFilter === 'due_soon') {
      filtered = todos.filter((todo: Todo) => {
        if (!todo.due_date) return false
        const todoDate = new Date(todo.due_date)
        return todoDate >= today && todoDate <= endOfWeek
      })
    }

    // Separate undated todos for "all" filter
    const undatedTodos = timeFilter === 'all' ? todos.filter((todo: Todo) => !todo.due_date) : []

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim()
      filtered = filtered.filter((todo: Todo) =>
        todo.title.toLowerCase().includes(query) ||
        todo.description?.toLowerCase().includes(query) ||
        todo.tags?.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // For "all" filter, exclude undated todos from the main list since they're shown separately
    if (timeFilter === 'all') {
      filtered = filtered.filter((todo: Todo) => todo.due_date)
    }

    // Sort to-dos
    const sorted = filtered.sort((a: Todo, b: Todo) => {
      const aCompleted = getEffectiveCompletedState(a)
      const bCompleted = getEffectiveCompletedState(b)
      
      // Incomplete to-dos first
      if (aCompleted !== bCompleted) {
        return aCompleted ? 1 : -1
      }
      
      // Then by due date
      const aDate = a.due_date ? new Date(a.due_date) : null
      const bDate = b.due_date ? new Date(b.due_date) : null
      
      if (!aDate && !bDate) {
        return a.title.localeCompare(b.title)
      }
      if (!aDate) return 1
      if (!bDate) return -1
      
      return aDate.getTime() - bDate.getTime()
    })

    return { allTodosFiltered: sorted, undatedTodos }
  }, [todos, timeFilter, searchQuery, getEffectiveCompletedState, today, endOfWeek])

  return {
    allTodosFiltered,
    undatedTodos,
    today,
    endOfWeek,
  }
}

