import React, { useState, useRef, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Send, Bot, User, Sparkles, Loader2, RefreshCw } from 'lucide-react'
import { agentAPI, tasksAPI } from '../../lib/api/sdk'
import { cn } from '../../lib/utils'
import { toast } from '../../lib/toast'
import type { AgentMessage } from '../../types'

interface AgentChatProps {
  className?: string
}

export function AgentChat({ className }: AgentChatProps) {
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: 'welcome',
      text: "Hi! I'm your AI agent. I can help you manage tasks, schedule your day, analyze your productivity, and answer questions. What would you like to work on?",
      isUser: false,
      timestamp: new Date().toISOString(),
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Get tasks for context
  const { data: tasks } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const result = await tasksAPI.getTasks()
      if (result.error) throw new Error(result.error)
      return result.data || []
    },
  })

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const result = await agentAPI.sendQuery({
        query: message,
        context: {
          currentPage: 'agent',
          recentTasks: tasks?.slice(0, 5) || [],
          conversationId,
        }
      })
      if (result.error) throw new Error(result.error)
      return result.data
    },
    onSuccess: (response) => {
      if (response?.conversationId) {
        setConversationId(response.conversationId)
      }

      const aiMessage: AgentMessage = {
        id: Date.now().toString(),
        text: response?.message || response?.data?.response || 'I received your message but had trouble generating a response.',
        isUser: false,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, aiMessage])
    },
    onError: (error) => {
      const errorMessage: AgentMessage = {
        id: Date.now().toString(),
        text: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        isUser: false,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMessage])
      toast.error('Failed to send message', error instanceof Error ? error.message : 'Please try again')
    },
  })

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || sendMessageMutation.isPending) return

    const userMessage: AgentMessage = {
      id: Date.now().toString(),
      text: inputValue.trim(),
      isUser: true,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')

    sendMessageMutation.mutate(inputValue.trim())
  }

  const quickActions = [
    { text: "What should I work on next?", icon: Sparkles },
    { text: "Create a task for tomorrow", icon: Bot },
    { text: "Show my productivity stats", icon: RefreshCw },
    { text: "Schedule my week", icon: Sparkles },
  ]

  const handleQuickAction = (text: string) => {
    setInputValue(text)
    inputRef.current?.focus()
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-3",
              message.isUser ? "justify-end" : "justify-start"
            )}
          >
            {!message.isUser && (
              <div className="flex-shrink-0 w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-primary" />
              </div>
            )}
            
            <div
              className={cn(
                "max-w-[80%] p-3 rounded-lg",
                message.isUser
                  ? "bg-primary text-white ml-auto"
                  : "bg-surface text-textPrimary"
              )}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                {message.text}
              </p>
              <div className={cn(
                "text-xs mt-1 opacity-70",
                message.isUser ? "text-white/70" : "text-textSecondary"
              )}>
                {new Date(message.timestamp).toLocaleTimeString([], { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </div>
            </div>

            {message.isUser && (
              <div className="flex-shrink-0 w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {sendMessageMutation.isPending && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center">
              <Bot className="w-4 h-4 text-primary" />
            </div>
            <div className="bg-surface text-textPrimary p-3 rounded-lg">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm text-textSecondary">Agent is thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {messages.length <= 1 && !sendMessageMutation.isPending && (
        <div className="p-4 border-t border-gray-700">
          <p className="text-sm text-textSecondary mb-3">Try asking:</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {quickActions.map((action, index) => {
              const Icon = action.icon
              return (
                <button
                  key={index}
                  onClick={() => handleQuickAction(action.text)}
                  className="flex items-center gap-2 p-2 text-left text-sm bg-surface hover:bg-gray-600 rounded-lg transition-colors"
                >
                  <Icon className="w-4 h-4 text-primary flex-shrink-0" />
                  <span className="text-textPrimary">{action.text}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask me anything about your tasks, schedule, or productivity..."
            disabled={sendMessageMutation.isPending}
            className="input flex-1"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || sendMessageMutation.isPending}
            className={cn(
              "px-4 py-2 bg-primary text-white rounded-lg transition-colors flex items-center justify-center",
              (!inputValue.trim() || sendMessageMutation.isPending)
                ? "opacity-50 cursor-not-allowed"
                : "hover:bg-primary/90"
            )}
          >
            {sendMessageMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </form>
    </div>
  )
}