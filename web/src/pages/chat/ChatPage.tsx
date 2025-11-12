import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { agentAPI, commandsAPI } from '@/lib/api/sdk'
import { CommandInput } from '@/components/commands'
import { AnimatedThinkingText, PulseTrace, MarkdownText, CollapsibleSearchResults } from '@/components/ui/common'
import { TaskSuccessCard, CollapsibleTaskList } from '@/components/tasks'
import { SimpleSuccessCard } from '@/components/cards'
import { SchedulingWorkflowCard } from '@/components/scheduling'
import { extractParameters } from '@/lib/commands/extractors'
import { getCommand } from '@/lib/commands/definitions'
import { useTaskSuccess } from '@/contexts/TaskSuccessContext'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import type { Task } from '@/types'
import { TODO_CACHE_KEYS } from '@/hooks/shared'

interface ConversationalMetadata {
  operation?: string
  entity_type?: string
  task_count?: number
  tasks?: Task[]
  card?: SimpleSuccessCardData
  can_retry?: boolean
  retry_suggestion?: string
  found_tasks?: Task[]
  task_options?: Task[]
  original_query?: string
  workflow_context?: Record<string, unknown>
}

interface SearchData {
  results?: unknown[]
  query?: string
  [key: string]: unknown
}

interface SimpleSuccessCardData {
  operation: string
  entityType: string
  entityTitle: string
  card: {
    operation: string
    entity_type: string
    entity_title: string
    acknowledgement_message?: string
    details?: Record<string, unknown>
    [key: string]: unknown
  }
  acknowledgementMessage?: string
}

interface ScheduleData {
  schedule?: Array<{
    title: string
    start_time: string
    end_time: string
    duration?: number
    type?: string
  }>
  commit_info?: {
    blocks_committed: number
    status: string
  }
  message?: string
  status?: string
}

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
  type?: 'text' | 'task_success' | 'conversational' | 'search_results' | 'simple_success' | 'scheduling_workflow'
  task?: Task
  metadata?: ConversationalMetadata
  searchData?: SearchData
  successCard?: SimpleSuccessCardData
  scheduleData?: ScheduleData
}

interface ChatPageProps {
  initialMessage?: string
}

function ChatPageCore({ initialMessage }: ChatPageProps) {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const taskSuccess = useTaskSuccess()
  const [messages, setMessages] = useState<Message[]>([])
  const [messageText, setMessageText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>(undefined)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const hasInitialized = useRef(false)

  // Function to add task success message to chat
  const addTaskSuccessMessage = (task: Task) => {
    const taskMessage: Message = {
      id: `task-success-${Date.now()}`,
      text: '', // Empty text since we'll render the TaskSuccessCard
      isUser: false,
      timestamp: new Date(),
      type: 'task_success',
      task: task
    }
    setMessages(prev => [...prev, taskMessage])
    
    // Clear thinking indicator when task card appears
    setIsTyping(false)
  }

  // Function to add conversational response to chat
  const addConversationalMessage = (message: string, metadata?: ConversationalMetadata) => {
    const conversationalMessage: Message = {
      id: `conversational-${Date.now()}`,
      text: message,
      isUser: false,
      timestamp: new Date(),
      type: 'conversational',
      metadata: metadata
    }
    setMessages(prev => [...prev, conversationalMessage])
  }

  // Function to add search results to chat
  const addSearchResults = (searchData: SearchData) => {
    // Don't add separate messages - everything will be in the task card
    // The task card will be updated with the search results
  }

  // Function to add simple success card to chat
  const addSimpleSuccessCard = (operation: string, entityType: string, entityTitle: string, card: Record<string, unknown>, acknowledgementMessage?: string) => {
    const successMessage: Message = {
      id: `simple-success-${Date.now()}`,
      text: '', // Empty text since we'll render the SimpleSuccessCard
      isUser: false,
      timestamp: new Date(),
      type: 'simple_success',
      successCard: { operation, entityType, entityTitle, card, acknowledgementMessage }
    }
    setMessages(prev => [...prev, successMessage])
    
    // Clear thinking indicator when success card appears
    setIsTyping(false)
  }

  // Function to update existing task
  const updateTask = (taskId: string, updates: Partial<Task>) => {
    setMessages(prev => prev.map(message => {
      if (message.type === 'task_success' && message.task?.id === taskId) {
        return {
          ...message,
          task: { ...message.task, ...updates }
        }
      }
      return message
    }))
  }

  // Function to add scheduling workflow card
  const addSchedulingWorkflowCard = () => {
    console.log('[ChatPage] addSchedulingWorkflowCard called')
    const schedulingMessage: Message = {
      id: `scheduling-workflow-${Date.now()}`,
      text: '',
      isUser: false,
      timestamp: new Date(),
      type: 'scheduling_workflow'
    }
    console.log('[ChatPage] Adding scheduling message:', schedulingMessage)
    setMessages(prev => [...prev, schedulingMessage])

    // Clear thinking indicator when workflow card appears
    setIsTyping(false)
  }

  // Function to update scheduling workflow card with results
  const updateSchedulingWorkflowCard = (scheduleData: ScheduleData) => {
    console.log('[ChatPage] updateSchedulingWorkflowCard called with data:', scheduleData)
    setMessages(prev => prev.map(message => {
      if (message.type === 'scheduling_workflow' && !message.scheduleData) {
        return {
          ...message,
          scheduleData: scheduleData
        }
      }
      return message
    }))
  }

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Register the task success message function with context
  useEffect(() => {
    taskSuccess.registerTaskSuccessHandler(addTaskSuccessMessage)
    taskSuccess.registerConversationalHandler(addConversationalMessage)
    taskSuccess.registerSearchResultsHandler(addSearchResults)
    taskSuccess.registerUpdateTaskHandler(updateTask)
    taskSuccess.registerSimpleSuccessHandler(addSimpleSuccessCard)
    taskSuccess.registerSchedulingWorkflowHandler(addSchedulingWorkflowCard)
    taskSuccess.registerSchedulingCompletionHandler(updateSchedulingWorkflowCard)
  }, [taskSuccess, addTaskSuccessMessage, addConversationalMessage, addSearchResults, updateTask, addSimpleSuccessCard, addSchedulingWorkflowCard, updateSchedulingWorkflowCard])

  // Send initial message if provided
  useEffect(() => {
    if (!hasInitialized.current) {
      hasInitialized.current = true
      
      // Check for message from URL params first, then props
      const messageFromUrl = searchParams.get('message')
      const messageToSend = messageFromUrl || initialMessage
      
      if (messageToSend && messageToSend.trim()) {
        // Send initial message (sendMessage will add the user message)
        sendMessage(messageToSend.trim())
      } else {
        // Add just welcome message
        const welcomeMessage: Message = {
          id: 'welcome',
          text: getGreeting() + '! What can I help you with today?',
          isUser: false,
          timestamp: new Date()
        }
        setMessages([welcomeMessage])
      }
    }
  }, [initialMessage, searchParams])

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }

  const sendMessage = async (message: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      isUser: true,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    
    setIsTyping(true)
    
    try {
      // Check if this is a command (starts with /)
      if (message.trim().startsWith('/')) {
        // Execute command directly
        const commandParts = message.trim().slice(1).split(/\s+/)
        const commandName = commandParts[0]
        const commandText = commandParts.slice(1).join(' ')

        // Get command definition
        const command = getCommand(commandName)
        
        if (command) {
          // Extract parameters
          const parameters = extractParameters(commandText, command.id)
          
          // Execute command
          const commandResult = await commandsAPI.execute(
            commandName,
            parameters,
            message
          )

          // Check if this is a todo/task creation (command returns data with task/todo)
          if (commandResult.success && commandResult.result?.todo && commandName === 'todo') {
            const todo = commandResult.result.todo
            
            // Invalidate todo cache to refresh the UI
            queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
            
            // Show CRUD success card
            addSimpleSuccessCard(
              'created',
              'todo',
              todo.title,
              {
                details: {
                  created_tasks: [todo.title],
                  due_date: todo.due_date,
                  tags: todo.tags || [],
                  priority: todo.priority || 'medium'
                }
              },
              commandResult.immediate_response
            )
            return
          }

          // For other commands, just show the response message
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: commandResult.immediate_response,
            isUser: false,
            timestamp: new Date(),
            type: 'text'
          }
          setMessages(prev => [...prev, aiMessage])
          setIsTyping(false)
          return
        } else {
          // Unknown command - show help
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: `Unknown command: /${commandName}. Type /help to see available commands.`,
            isUser: false,
            timestamp: new Date(),
            type: 'text'
          }
          setMessages(prev => [...prev, aiMessage])
          setIsTyping(false)
          return
        }
      }

      // Regular message - use existing LLM flow
      const context = {
        currentPage: 'chat',
        timestamp: new Date().toISOString()
      }

      const response = await agentAPI.sendQuery({
        query: message,
        context: {
          ...context,
          conversation_id: conversationId,
          include_history: true
        }
      })

      // Debug logging only in development
      if (import.meta.env.DEV) {
        console.log('🔍 [FRONTEND] Response received:', { 
          success: response?.success,
          hasData: !!response?.data 
        })
      }

      // Store conversation_id from response for follow-up questions
      if ((response as any)?.conversation_id) {
        setConversationId((response as any).conversation_id)
      }

      // Handle successful responses - response is the AgentResponse directly
      if (response?.success !== false && response) {
        let responseText = ''
        
        // New structure: Check for agent immediate_response field
        if ((response as any).immediate_response) {
          responseText = (response as any).immediate_response
        }
        // Legacy: Check for chat workflow response from supervision
        else if (response.data && response.data.response) {
          responseText = response.data.response
        }
        // Check for message field (common response format)
        else if (response.data && response.data.message) {
          responseText = response.data.message
        }
        // Direct response field (legacy)
        else if ((response as any).response) {
          responseText = (response as any).response
        }
        // Direct message field
        else if (response.message) {
          responseText = response.message
        }
        // Check if response itself is a string
        else if (typeof response === 'string') {
          responseText = response
        }
        // Legacy structure support
        else if (response.data) {
          if (typeof response.data === 'string') {
            responseText = response.data
          }
          else if (response.data.summary) {
            responseText = response.data.summary
          }
        }
        // Handle clarification or other structured responses (legacy)
        else if ((response as any).conversation_type === 'processing') {
          responseText = "I'm processing your request. Could you please provide more details about what you'd like me to help you with?"
        }
        
        // Only add message to chat if we have response text and it's not a search task or CRUD operation
        const crudActions = ['task_management'] // CRUD operations that will show success cards
        const isCrudAction = crudActions.includes(response.intent) && ['create_task', 'update_task', 'delete_task', 'complete_task', 'list_tasks'].includes(response.action)
        
        // Check if this is a clarification request (should always be displayed)
        const isClarificationRequest = responseText && (
          responseText.includes('What task would you like me to create') ||
          responseText.includes('Could you please provide more details') ||
          responseText.includes('Please provide more details') ||
          responseText.includes('What would you like me to')
        )
        
        if (responseText && response.intent !== 'search' && (!isCrudAction || isClarificationRequest)) {
          console.log('✅ [FRONTEND] Extracted responseText:', responseText)

          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: responseText,
            isUser: false,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, aiMessage])
          
          // Clear thinking indicator for non-search tasks
          setIsTyping(false)
        } else if (responseText && response.intent === 'search') {
          console.log('✅ [FRONTEND] Search task - immediate response will be handled by task card')
          // Don't clear thinking indicator yet - wait for task card to appear
        } else if (isCrudAction && !isClarificationRequest) {
          console.log('✅ [FRONTEND] CRUD operation - immediate response will be handled by success card')
          // Clear thinking indicator for CRUD operations
          setIsTyping(false)
        } else {
          console.log('✅ [FRONTEND] No immediate response text - success card will handle the response')
          // Clear thinking indicator for other cases
          setIsTyping(false)
        }
      } else {
        // Handle error responses
        const errorText = response?.error || 'I encountered an issue processing your request. Could you try rephrasing it?'
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: errorText,
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
        setIsTyping(false)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error connecting to our servers. Please try again.',
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      setIsTyping(false)
    }
  }

  const handleSendMessage = () => {
    if (messageText.trim() === '' || isTyping) return
    
    const message = messageText.trim()
    setMessageText('')
    sendMessage(message)
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0f0f0f' }}>
      {/* Fixed Back Button */}
      <button 
        onClick={() => navigate('/')}
        className="fixed top-4 px-3 py-2 rounded-lg hover:bg-neutral-800/20 transition-colors z-50 group flex items-center gap-2"
        style={{ left: 'calc(var(--sidebar-width, 4rem) + 1rem)' }}
        aria-label="Back"
      >
        <ArrowLeft size={16} className="text-gray-400 group-hover:text-white transition-colors" />
        <span className="text-gray-400 group-hover:text-white transition-colors text-sm font-medium">Back</span>
      </button>

      {/* Messages Container - Centered within max-w-4xl */}
      <div className="flex-1 overflow-y-auto pt-24 pb-4">
        <div className="w-full max-w-4xl mx-auto px-6 space-y-6">
          {messages.map((message) => (
            <div key={message.id}>
              {message.isUser ? (
                // User message - Right aligned with gray bubble
                <div className="flex justify-end">
                  <div className="max-w-[85%] bg-[#2E2E30] rounded-3xl px-4 py-3">
                    <p className="text-white text-base leading-5 font-normal">{message.text}</p>
                  </div>
                </div>
              ) : (
                // AI message - Left aligned with icon and name
                <div className="flex gap-3">
                  <div className="w-8 h-8 flex items-center justify-center flex-shrink-0 mt-1">
                    <PulseTrace active={false} width={24} height={24} />
                  </div>
                  <div className="flex-1">
                    {message.type === 'task_success' && message.task ? (
                      <div className="space-y-4">
                        {/* Acknowledgement text for search tasks */}
                        {message.task.workflow_type === 'search' && message.task.description && (
                          <MarkdownText>
                            {message.task.description}
                          </MarkdownText>
                        )}
                        <TaskSuccessCard task={message.task} />
                        {/* Search answer as plain text after the card */}
                        {message.task.workflow_type === 'search' && message.task.status === 'completed' && message.task.result?.search_data?.answer && (
                          <MarkdownText>
                            {message.task.result.search_data.answer}
                          </MarkdownText>
                        )}
                      </div>
                    ) : message.type === 'conversational' && message.metadata?.operation === 'listed' && message.metadata?.entity_type === 'tasks' ? (
                      <div className="space-y-4">
                        <MarkdownText>
                          {message.text}
                        </MarkdownText>
                        {message.metadata.tasks && message.metadata.tasks.length > 0 && (
                          <CollapsibleTaskList 
                            tasks={message.metadata.tasks} 
                            taskCount={message.metadata.task_count} 
                          />
                        )}
                      </div>
                    ) : message.type === 'search_results' && message.searchData ? (
                      <div className="space-y-4">
                        <MarkdownText>
                          {message.text}
                        </MarkdownText>
                        <CollapsibleSearchResults searchData={message.searchData} />
                      </div>
                    ) : message.type === 'simple_success' && message.successCard ? (
                      <SimpleSuccessCard
                        operation={message.successCard.operation}
                        entityType={message.successCard.entityType}
                        entityTitle={message.successCard.entityTitle}
                        card={message.successCard.card}
                        acknowledgementMessage={message.successCard.acknowledgementMessage}
                      />
                    ) : message.type === 'scheduling_workflow' ? (
                      <SchedulingWorkflowCard scheduleData={message.scheduleData} />
                    ) : (
                      <MarkdownText>
                        {message.text || 'No text content'}
                      </MarkdownText>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {isTyping && (
            <div className="flex gap-3">
              <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
                <PulseTrace active={true} width={24} height={24} />
              </div>
              <div className="flex-1 flex items-center">
                <AnimatedThinkingText 
                  text="Thinking"
                  className="text-white text-lg leading-7 opacity-70"
                />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Container - Fixed at bottom, centered within max-w-4xl */}
      <div className="py-4" style={{ backgroundColor: '#0f0f0f' }}>
        <div className="w-full max-w-4xl mx-auto px-6">
          <CommandInput
            value={messageText}
            onChange={setMessageText}
            onSubmit={handleSendMessage}
            disabled={isTyping}
            placeholder="How can I help you today?"
          />
        </div>
      </div>
    </div>
  )
}

// Wrap with ErrorBoundary to prevent chat errors from breaking the entire app
export function ChatPage(props: ChatPageProps) {
  return (
    <ErrorBoundary>
      <ChatPageCore {...props} />
    </ErrorBoundary>
  )
}