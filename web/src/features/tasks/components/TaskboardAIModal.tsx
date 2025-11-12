import { useState, useEffect, useRef } from 'react'
import { X, Maximize2, Square, ChevronDown, Search, CheckSquare, FileText } from 'lucide-react'
import { CommandInput } from '../../../components/commands'
import { AnimatedThinkingText, PulseTrace } from '../../../components/ui/common'
import { agentAPI } from '../../../lib/api/sdk'

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}

interface TaskboardAIModalProps {
  visible: boolean
  onClose: () => void
  userName?: string
}

interface SuggestedAction {
  id: string
  icon: React.ReactNode
  text: string
  prompt: string
}

export function TaskboardAIModal({ visible, onClose, userName = 'there' }: TaskboardAIModalProps) {
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>(undefined)
  const [showSuggestedActions, setShowSuggestedActions] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Suggested actions for taskboard page
  const suggestedActions: SuggestedAction[] = [
    {
      id: 'search',
      icon: <Search size={16} className="text-white" />,
      text: 'Search for anything',
      prompt: 'Search for anything'
    },
    {
      id: 'organize',
      icon: <CheckSquare size={16} className="text-white" />,
      text: 'Organize my tasks',
      prompt: 'Help me organize my tasks by priority and due date'
    },
    {
      id: 'analyze',
      icon: <FileText size={16} className="text-white" />,
      text: 'Analyze my workload',
      prompt: 'Analyze my current workload and suggest a plan'
    },
    {
      id: 'tracker',
      icon: <CheckSquare size={16} className="text-white" />,
      text: 'Create a task tracker',
      prompt: 'Create a task tracker for my upcoming assignments'
    }
  ]

  // Initialize with greeting when modal opens
  useEffect(() => {
    if (visible) {
      setMessages([{
        id: 'greeting',
        text: `Hey ${userName}, how can I help?`,
        isUser: false,
        timestamp: new Date()
      }])
      setShowSuggestedActions(true)
      setInputValue('')
      
      // Focus input after a short delay
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    } else {
      // Reset when closing
      setMessages([])
      setInputValue('')
      setIsTyping(false)
    }
  }, [visible])

  // Hide suggested actions when user sends messages
  useEffect(() => {
    if (messages.length > 1) {
      setShowSuggestedActions(false)
    }
  }, [messages])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (promptText?: string) => {
    const textToSend = promptText || inputValue.trim()
    if (textToSend === '' || isTyping) return

    resetInactivityTimer()

    const userMessage: Message = {
      id: Date.now().toString(),
      text: textToSend,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    if (!promptText) setInputValue('')
    setIsTyping(true)

    try {
      const context = {
        currentPage: 'taskboard',
        timestamp: new Date().toISOString()
      }

      const response = await agentAPI.sendQuery({
        query: textToSend,
        context
      })

      // Store conversation_id if provided
      if ((response as any)?.conversation_id) {
        setConversationId((response as any).conversation_id)
      }

      let responseText = ''
      if (response?.success !== false && response) {
        if ((response as any).immediate_response) {
          responseText = (response as any).immediate_response
        } else if (response.data && response.data.response) {
          responseText = response.data.response
        } else if (response.data && response.data.message) {
          responseText = response.data.message
        } else if ((response as any).response) {
          responseText = (response as any).response
        } else if (response.message) {
          responseText = response.message
        } else if (typeof response === 'string') {
          responseText = response
        } else if (response.data) {
          if (typeof response.data === 'string') {
            responseText = response.data
          } else if (response.data.summary) {
            responseText = response.data.summary
          }
        }
      }

      if (responseText) {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: responseText,
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, aiMessage])
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleSuggestedAction = (action: SuggestedAction) => {
    handleSendMessage(action.prompt)
  }

  const inactivityTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const resetInactivityTimer = () => {
    if (inactivityTimeoutRef.current) {
      clearTimeout(inactivityTimeoutRef.current)
    }
    // Auto-close after 5 minutes of inactivity (optional - can remove if not needed)
    inactivityTimeoutRef.current = setTimeout(() => {
      if (!isTyping && messages.length > 1) {
        // Optional: auto-close after inactivity
        // onClose()
      }
    }, 300000) // 5 minutes
  }

  // Handle escape key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && visible) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [visible, onClose])

  if (!visible) return null

  return (
    <>
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
      <div 
        className="fixed bottom-6 right-6 z-50 w-[400px] h-[520px] rounded-2xl flex flex-col overflow-hidden shadow-2xl"
        style={{ 
          backgroundColor: '#1a1a1a',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          animation: 'fadeInUp 0.3s ease-out'
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-2 text-white text-sm font-medium hover:bg-white/5 px-2 py-1 rounded transition-colors">
              <span>New AI chat</span>
              <ChevronDown size={14} className="text-gray-400" />
            </button>
          </div>
          <div className="flex items-center gap-1">
            <button
              className="p-1.5 hover:bg-white/5 rounded transition-colors"
              title="Expand"
            >
              <Maximize2 size={14} className="text-gray-400 hover:text-white" />
            </button>
            <button
              className="p-1.5 hover:bg-white/5 rounded transition-colors"
              title="Minimize"
            >
              <Square size={14} className="text-gray-400 hover:text-white" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-white/5 rounded transition-colors"
              title="Close"
            >
              <X size={14} className="text-gray-400 hover:text-white" />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {/* AI Avatar and Greeting */}
          {messages.length === 1 && (
            <div className="flex gap-3 mb-6">
              <div className="w-8 h-8 flex items-center justify-center flex-shrink-0 mt-1">
                <PulseTrace active={false} width={24} height={24} />
              </div>
              <div className="flex-1">
                <p className="text-white text-lg font-semibold leading-tight">
                  {messages[0].text}
                </p>
              </div>
            </div>
          )}

          {/* Suggested Actions */}
          {showSuggestedActions && messages.length === 1 && (
            <div className="space-y-2 mb-6">
              {suggestedActions.map((action) => (
                <button
                  key={action.id}
                  onClick={() => handleSuggestedAction(action)}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-white/5 transition-colors text-left group"
                >
                  {action.icon}
                  <span className="text-white text-sm flex-1">{action.text}</span>
                  {action.id === 'tracker' && (
                    <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded">
                      New
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Messages */}
          {messages.length > 1 && (
            <div className="space-y-4">
              {messages.slice(1).map((message) => (
                <div key={message.id}>
                  {message.isUser ? (
                    // User message - Right aligned with gray bubble (matching ChatPage)
                    <div className="flex justify-end">
                      <div className="max-w-[85%] bg-[#2E2E30] rounded-3xl px-4 py-3">
                        <p className="text-white text-base leading-5 font-normal">{message.text}</p>
                      </div>
                    </div>
                  ) : (
                    // AI message - Left aligned with avatar (matching ChatPage)
                    <div className="flex gap-3">
                      <div className="w-8 h-8 flex items-center justify-center flex-shrink-0 mt-1">
                        <PulseTrace active={false} width={24} height={24} />
                      </div>
                      <div className="flex-1">
                        <p className="text-white text-base leading-5">{message.text}</p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Typing indicator */}
          {isTyping && (
            <div className="flex gap-3">
              <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
                <PulseTrace active={true} width={24} height={24} />
              </div>
              <div className="flex-1 flex items-center">
                <AnimatedThinkingText 
                  text="Thinking"
                  className="text-gray-400 text-sm"
                />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="px-6 py-4">
          <CommandInput
            value={inputValue}
            onChange={setInputValue}
            onSubmit={() => handleSendMessage()}
            disabled={isTyping}
            placeholder="Ask, search, or make anything..."
            showCommands={true}
          />
        </div>
      </div>
    </>
  )
}

