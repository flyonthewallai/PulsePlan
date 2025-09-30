import React, { useState, useEffect, useRef } from 'react'
import { Paperclip, ArrowUp, BrainCircuit } from 'lucide-react'
import { agentAPI } from '../lib/api/sdk'
import AnimatedThinkingText from '../components/AnimatedThinkingText'
import { TaskSuccessCard } from '../components/TaskSuccessCard'
import { CollapsibleTaskList } from '../components/CollapsibleTaskList'
import { CollapsibleSearchResults } from '../components/CollapsibleSearchResults'
import { MarkdownText } from '../components/MarkdownText'
import { SimpleSuccessCard } from '../components/SimpleSuccessCard'
import { setGlobalAddTaskSuccessMessage, setGlobalAddConversationalMessage, setGlobalAddSearchResults, setGlobalUpdateTask, setGlobalAddSimpleSuccessCard } from '../contexts/TaskSuccessContext'

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
  type?: 'text' | 'task_success' | 'conversational' | 'search_results' | 'simple_success'
  task?: any // Task data for success cards
  metadata?: any // Metadata for conversational responses
  searchData?: any // Search results data
  successCard?: any // Simple success card data
}

interface ChatPageProps {
  initialMessage?: string
  onBack?: () => void
}

export function ChatPage({ initialMessage, onBack }: ChatPageProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [messageText, setMessageText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const hasInitialized = useRef(false)

  // Function to add task success message to chat
  const addTaskSuccessMessage = (task: any) => {
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
  const addConversationalMessage = (message: string, metadata?: any) => {
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
  const addSearchResults = (searchData: any) => {
    console.log('🔍 addSearchResults called with:', searchData)
    
    // Don't add separate messages - everything will be in the task card
    // The task card will be updated with the search results
  }

  // Function to add simple success card to chat
  const addSimpleSuccessCard = (operation: string, entityType: string, entityTitle: string, card: any, acknowledgementMessage?: string) => {
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
  const updateTask = (taskId: string, updates: any) => {
    console.log('🔄 updateTask called with:', taskId, updates)
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

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Register the task success message function
  useEffect(() => {
    console.log('🔍 Registering global functions')
    setGlobalAddTaskSuccessMessage(addTaskSuccessMessage)
    setGlobalAddConversationalMessage(addConversationalMessage)
    setGlobalAddSearchResults(addSearchResults)
    setGlobalUpdateTask(updateTask)
    setGlobalAddSimpleSuccessCard(addSimpleSuccessCard)
    console.log('🔍 Global functions registered')
    return () => {
      setGlobalAddTaskSuccessMessage(() => {})
      setGlobalAddConversationalMessage(() => {})
      setGlobalAddSearchResults(() => {})
      setGlobalUpdateTask(() => {})
      setGlobalAddSimpleSuccessCard(() => {})
    }
  }, [addTaskSuccessMessage, addConversationalMessage, addSearchResults, updateTask, addSimpleSuccessCard])

  // Send initial message if provided
  useEffect(() => {
    if (initialMessage && initialMessage.trim() && !hasInitialized.current) {
      hasInitialized.current = true
      
      // Add welcome message first
      const welcomeMessage: Message = {
        id: 'welcome',
        text: getGreeting() + '! What can I help you with today?',
        isUser: false,
        timestamp: new Date()
      }
      setMessages([welcomeMessage])
      
      // Send initial message
      sendMessage(initialMessage.trim())
    } else if (!initialMessage && !hasInitialized.current) {
      hasInitialized.current = true
      
      // Add just welcome message
      const welcomeMessage: Message = {
        id: 'welcome',
        text: getGreeting() + '! What can I help you with today?',
        isUser: false,
        timestamp: new Date()
      }
      setMessages([welcomeMessage])
    }
  }, []) // Empty dependency array to run only once

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
      const context = {
        currentPage: 'chat',
        timestamp: new Date().toISOString()
      }

      const response = await agentAPI.sendQuery({
        query: message,
        context
      })

      console.log('🔍 [FRONTEND] Full response object:', response)
      console.log('🔍 [FRONTEND] response type:', typeof response)
      console.log('🔍 [FRONTEND] response keys:', Object.keys(response))
      console.log('🔍 [FRONTEND] response.immediate_response:', (response as any)?.immediate_response)
      console.log('🔍 [FRONTEND] response.success:', response?.success)

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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="min-h-screen bg-neutral-900 flex flex-col">
      {/* Header */}
      <div className="w-full px-6 py-4 flex items-center justify-between">
        {onBack && (
          <button 
            onClick={onBack}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ← Back
          </button>
        )}
        <div></div> {/* Spacer for centering */}
        <div></div> {/* Spacer for centering */}
      </div>

      {/* Messages Container - Centered within max-w-4xl */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
            <div key={message.id}>
              {message.isUser ? (
                // User message - Right aligned with gray bubble
                <div className="flex justify-end">
                  <div className="max-w-[85%] bg-[#3C3C3E] rounded-3xl px-4 py-3">
                    <p className="text-white text-base leading-5 font-normal">{message.text}</p>
                  </div>
                </div>
              ) : (
                // AI message - Left aligned with icon and name
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-neutral-800 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                    <BrainCircuit size={24} className="text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-white font-bold text-base mb-2">Pulse</div>
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
              <div className="w-8 h-8 bg-neutral-800 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                <BrainCircuit size={24} className="text-white" />
              </div>
              <div className="flex-1">
                <div className="text-white font-bold text-base mb-2">Pulse</div>
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
      <div className="px-6 py-4 bg-neutral-900">
        <div className="max-w-4xl mx-auto">
          <div className="bg-neutral-800/80 border border-gray-700/50 rounded-2xl p-3">
            <div className="flex items-center gap-2">
              <textarea
                placeholder="Message"
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 bg-transparent text-white placeholder-gray-400 text-base focus:outline-none min-h-[42px] max-h-32 resize-none"
                rows={1}
                style={{
                  height: 'auto',
                  minHeight: '42px',
                  maxHeight: '128px',
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = Math.min(target.scrollHeight, 128) + 'px';
                }}
              />
            </div>
            <div className="flex justify-between items-center mt-1.5">
              <button className="p-1">
                <Paperclip size={16} className="text-gray-400 hover:text-gray-300 transition-colors" />
              </button>
              <button
                onClick={handleSendMessage}
                disabled={messageText.trim() === '' || isTyping}
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all bg-white hover:bg-gray-100 ${
                  messageText.trim() === '' || isTyping
                    ? 'opacity-30 cursor-not-allowed' 
                    : 'opacity-100'
                }`}
              >
                <ArrowUp size={16} className="text-black" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}