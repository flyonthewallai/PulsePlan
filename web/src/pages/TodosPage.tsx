import React, { useState, useEffect } from 'react'
import { 
  Search, 
  ArrowUpDown, 
  Filter, 
  Plus, 
  CheckCircle2, 
  Circle,
  MoreHorizontal,
  Edit2,
  Trash2
} from 'lucide-react'
import { todosService } from '../services/todosService'

// Define all interfaces locally to avoid import issues
interface Todo {
  id: string
  user_id: string
  title: string
  description?: string
  completed: boolean
  priority: 'low' | 'medium' | 'high'
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  due_date?: string
  tags: string[]
  created_at: string
  completed_at?: string
  updated_at: string
}

interface CreateTodoData {
  title: string
  description?: string
  priority?: 'low' | 'medium' | 'high'
  due_date?: string
  tags?: string[]
}

interface UpdateTodoData {
  title?: string
  description?: string
  completed?: boolean
  priority?: 'low' | 'medium' | 'high'
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  due_date?: string
  tags?: string[]
}

interface TodoFilters {
  completed?: boolean
  priority?: 'low' | 'medium' | 'high'
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  tags?: string[]
}
import { Button } from '../components/ui/button'
import { cn } from '../lib/utils'

type ViewMode = 'active' | 'done'

export function TodosPage() {
  const [todos, setTodos] = useState<Todo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('active')
  const [searchQuery, setSearchQuery] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null)
  const [hoveredTodo, setHoveredTodo] = useState<string | null>(null)

  // Load todos on component mount
  useEffect(() => {
    loadTodos()
  }, [viewMode])

  // Add some sample todos for demonstration
  useEffect(() => {
    if (todos.length === 0 && !loading) {
      const sampleTodos: Todo[] = [
        {
          id: '1',
          user_id: 'demo-user',
          title: 'Make a new phantom for hiring emails',
          description: '',
          completed: false,
          priority: 'high',
          status: 'pending',
          tags: ['hiring'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '2',
          user_id: 'demo-user',
          title: 'Make it so the integrations page does not refetch every time',
          description: '',
          completed: false,
          priority: 'medium',
          status: 'pending',
          tags: ['engineering'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '3',
          user_id: 'demo-user',
          title: 'Submit video for Google Tasks',
          description: '',
          completed: false,
          priority: 'medium',
          status: 'pending',
          tags: ['engineering'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '4',
          user_id: 'demo-user',
          title: 'Work on SEO/performance using lighthouse',
          description: '',
          completed: false,
          priority: 'medium',
          status: 'pending',
          tags: ['engineering', 'growth'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '5',
          user_id: 'demo-user',
          title: 'Add cancellation policy and make a process for resolving disputes, and tell Harold about it next week',
          description: '',
          completed: false,
          priority: 'medium',
          status: 'pending',
          tags: ['admin'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '6',
          user_id: 'demo-user',
          title: 'Link support in notes and todos',
          description: '',
          completed: false,
          priority: 'low',
          status: 'pending',
          tags: ['engineering'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '7',
          user_id: 'demo-user',
          title: 'Weekly briefings should have day of week setting',
          description: '',
          completed: false,
          priority: 'low',
          status: 'pending',
          tags: ['engineering'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '8',
          user_id: 'demo-user',
          title: 'Model switcher on iOS app',
          description: '',
          completed: false,
          priority: 'low',
          status: 'pending',
          tags: ['engineering'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '9',
          user_id: 'demo-user',
          title: 'Notes formatting improvements for LLM',
          description: '',
          completed: false,
          priority: 'low',
          status: 'pending',
          tags: ['engineering'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '10',
          user_id: 'demo-user',
          title: 'Debug ads',
          description: '',
          completed: false,
          priority: 'low',
          status: 'pending',
          tags: ['engineering'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]
      setTodos(sampleTodos)
    }
  }, [todos.length, loading])

  const loadTodos = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const filters: TodoFilters = {
        completed: viewMode === 'done'
      }
      
      const { data, error } = await todosService.getTodos(filters)
      
      if (error) {
        setError(error)
      } else {
        setTodos(data || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load todos')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleCompletion = async (todo: Todo) => {
    try {
      const { data, error } = await todosService.toggleTodoCompletion(todo.id, !todo.completed)
      
      if (error) {
        setError(error)
      } else if (data) {
        setTodos(prev => prev.map(t => t.id === todo.id ? data : t))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update todo')
    }
  }

  const handleDeleteTodo = async (todoId: string) => {
    try {
      const { error } = await todosService.deleteTodo(todoId)
      
      if (error) {
        setError(error)
      } else {
        setTodos(prev => prev.filter(t => t.id !== todoId))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete todo')
    }
  }

  const handleCreateTodo = async (todoData: CreateTodoData) => {
    try {
      const { data, error } = await todosService.createTodo(todoData)
      
      if (error) {
        setError(error)
      } else if (data) {
        setTodos(prev => [data, ...prev])
        setShowAddModal(false)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create todo')
    }
  }

  const filteredTodos = todos.filter(todo => 
    todo.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    todo.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    todo.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-500'
      case 'medium': return 'text-yellow-500'
      case 'low': return 'text-green-500'
      default: return 'text-gray-500'
    }
  }

  const getPriorityLabel = (priority: string) => {
    switch (priority) {
      case 'high': return 'P0'
      case 'medium': return 'P1'
      case 'low': return 'P2'
      default: return 'P1'
    }
  }

  const getCategoryColor = (tag: string) => {
    const colors: Record<string, string> = {
      'hiring': 'bg-green-500',
      'engineering': 'bg-yellow-500',
      'admin': 'bg-blue-500',
      'legal': 'bg-blue-500',
      'growth': 'bg-red-500',
      'personal': 'bg-purple-500',
      'shopping': 'bg-orange-500',
      'school': 'bg-indigo-500',
      'homework': 'bg-indigo-500',
    }
    
    const normalizedTag = tag.toLowerCase()
    return colors[normalizedTag] || 'bg-gray-500'
  }

  const getCategoryLabel = (tag: string) => {
    const labels: Record<string, string> = {
      'admin': 'Admin/Legal',
      'legal': 'Admin/Legal',
    }
    
    const normalizedTag = tag.toLowerCase()
    return labels[normalizedTag] || tag
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
        <div className="text-white">Loading todos...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neutral-900 flex flex-col items-center">
      <div className="w-full max-w-4xl px-6 pt-24 pb-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-white">To-dos</h1>
          
          {/* View Toggle */}
          <div className="flex items-center bg-neutral-800 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('active')}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
                viewMode === 'active'
                  ? 'bg-white text-black'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              Active
            </button>
            <button
              onClick={() => setViewMode('done')}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
                viewMode === 'done'
                  ? 'bg-white text-black'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              Done
            </button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="relative">
              <Search size={16} className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search todos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-neutral-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none text-sm"
              />
            </div>

            {/* Sort */}
            <button className="p-2 text-gray-400 hover:text-white transition-colors">
              <ArrowUpDown size={20} />
            </button>

            {/* Filter */}
            <button className="p-2 text-gray-400 hover:text-white transition-colors">
              <Filter size={20} />
            </button>
          </div>

          {/* Add Button */}
          <button
            onClick={() => setShowAddModal(true)}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <Plus size={20} />
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/20 border border-red-500/50 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Todos List */}
        <div className="space-y-2">
          {filteredTodos.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-lg">
                {viewMode === 'active' ? 'No active todos' : 'No completed todos'}
              </div>
              <div className="text-gray-500 text-sm mt-2">
                {viewMode === 'active' ? 'Add a new todo to get started' : 'Complete some todos to see them here'}
              </div>
            </div>
          ) : (
            filteredTodos.map((todo) => (
              <div
                key={todo.id}
                className="flex items-center gap-4 p-4 bg-neutral-800 rounded-lg hover:bg-neutral-750 transition-colors group"
                onMouseEnter={() => setHoveredTodo(todo.id)}
                onMouseLeave={() => setHoveredTodo(null)}
              >
                {/* Checkbox */}
                <button
                  onClick={() => handleToggleCompletion(todo)}
                  className="flex-shrink-0"
                >
                  {todo.completed ? (
                    <CheckCircle2 size={20} className="text-green-500" />
                  ) : (
                    <Circle size={20} className="text-gray-400 hover:text-white transition-colors" />
                  )}
                </button>

                {/* Todo Content */}
                <div className="flex-1 min-w-0">
                  <div className={cn(
                    'text-white text-base',
                    todo.completed && 'line-through text-gray-400'
                  )}>
                    {todo.title}
                  </div>
                  {todo.description && (
                    <div className="text-gray-400 text-sm mt-1">
                      {todo.description}
                    </div>
                  )}
                </div>

                {/* Tags */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Priority */}
                  <span className={cn(
                    'px-2 py-1 rounded-full text-xs font-medium',
                    getPriorityColor(todo.priority),
                    'bg-neutral-700'
                  )}>
                    {getPriorityLabel(todo.priority)}
                  </span>

                  {/* Category Tags */}
                  {todo.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium text-white bg-neutral-700"
                    >
                      <div className={cn('w-2 h-2 rounded-full', getCategoryColor(tag))} />
                      {getCategoryLabel(tag)}
                    </span>
                  ))}
                </div>

                {/* Actions */}
                <div className={cn(
                  'flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity',
                  hoveredTodo === todo.id && 'opacity-100'
                )}>
                  <button
                    onClick={() => setEditingTodo(todo)}
                    className="p-1 text-gray-400 hover:text-white transition-colors"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    onClick={() => handleDeleteTodo(todo.id)}
                    className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add Todo Modal */}
      {showAddModal && (
        <AddTodoModal
          onClose={() => setShowAddModal(false)}
          onSave={handleCreateTodo}
        />
      )}

      {/* Edit Todo Modal */}
      {editingTodo && (
        <EditTodoModal
          todo={editingTodo}
          onClose={() => setEditingTodo(null)}
          onSave={(updates) => {
            // Handle update logic here
            setEditingTodo(null)
          }}
        />
      )}
    </div>
  )
}

// Add Todo Modal Component
interface AddTodoModalProps {
  onClose: () => void
  onSave: (data: CreateTodoData) => void
}

function AddTodoModal({ onClose, onSave }: AddTodoModalProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium')
  const [tags, setTags] = useState<string[]>([])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (title.trim()) {
      onSave({
        title: title.trim(),
        description: description.trim() || undefined,
        priority,
        tags: tags.length > 0 ? tags : undefined,
      })
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-neutral-800 rounded-lg p-6 w-full max-w-md mx-4">
        <h2 className="text-xl font-bold text-white mb-4">Add New Todo</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter todo title..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Description (optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter description..."
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as 'low' | 'medium' | 'high')}
              className="w-full px-3 py-2 bg-neutral-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low (P2)</option>
              <option value="medium">Medium (P1)</option>
              <option value="high">High (P0)</option>
            </select>
          </div>

          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!title.trim()}
            >
              Add Todo
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Edit Todo Modal Component
interface EditTodoModalProps {
  todo: Todo
  onClose: () => void
  onSave: (updates: any) => void
}

function EditTodoModal({ todo, onClose, onSave }: EditTodoModalProps) {
  const [title, setTitle] = useState(todo.title)
  const [description, setDescription] = useState(todo.description || '')
  const [priority, setPriority] = useState(todo.priority)
  const [tags, setTags] = useState(todo.tags)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      title: title.trim(),
      description: description.trim() || undefined,
      priority,
      tags: tags.length > 0 ? tags : [],
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-neutral-800 rounded-lg p-6 w-full max-w-md mx-4">
        <h2 className="text-xl font-bold text-white mb-4">Edit Todo</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as 'low' | 'medium' | 'high')}
              className="w-full px-3 py-2 bg-neutral-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low (P2)</option>
              <option value="medium">Medium (P1)</option>
              <option value="high">High (P0)</option>
            </select>
          </div>

          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!title.trim()}
            >
              Save Changes
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
