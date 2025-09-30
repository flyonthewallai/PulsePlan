import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Bot, 
  Sparkles, 
  Clock, 
  Calendar, 
  Target, 
  TrendingUp,
  MessageSquare,
  Settings,
  HelpCircle
} from 'lucide-react'
import { AgentChat } from '../features/ai/AgentChat'
import { tasksAPI } from '../lib/api/sdk'
import { getGreeting } from '../lib/utils'

export function AgentPage() {
  const [showChat, setShowChat] = useState(true)
  
  // Get tasks for context
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const result = await tasksAPI.getTasks()
      if (result.error) throw new Error(result.error)
      return result.data || []
    },
  })

  const pendingTasks = tasks?.filter(task => task.status === 'pending') || []
  const inProgressTasks = tasks?.filter(task => task.status === 'in_progress') || []
  const completedToday = tasks?.filter(task => {
    const today = new Date().toDateString()
    return task.status === 'completed' && new Date(task.due_date).toDateString() === today
  }) || []

  const quickPrompts = [
    {
      category: "Task Management",
      icon: Target,
      prompts: [
        "What should I prioritize today?",
        "Create a task for my upcoming project",
        "Show me my completed tasks",
        "Break down my large tasks into smaller ones"
      ]
    },
    {
      category: "Scheduling",
      icon: Calendar,
      prompts: [
        "Plan my week based on my tasks",
        "When should I work on my high-priority items?",
        "Find time for a 2-hour study session",
        "Reschedule my tasks for optimal productivity"
      ]
    },
    {
      category: "Productivity",
      icon: TrendingUp,
      prompts: [
        "How productive was I this week?",
        "Show me my completion patterns",
        "Suggest ways to improve my workflow",
        "What are my peak productivity hours?"
      ]
    },
    {
      category: "Analysis",
      icon: Clock,
      prompts: [
        "Analyze my task completion rate",
        "Which subjects take me the longest?",
        "Show me trends in my productivity",
        "Compare this week to last week"
      ]
    }
  ]

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-textPrimary flex items-center gap-3">
            <div className="p-2 bg-primary/20 rounded-lg">
              <Bot className="w-6 h-6 text-primary" />
            </div>
            AI Agent
          </h1>
          <p className="text-textSecondary mt-1">
            {getGreeting()}! I'm here to help with tasks, scheduling, and productivity insights.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowChat(!showChat)}
            className={`btn-secondary flex items-center gap-2 ${
              showChat ? 'bg-primary/20 text-primary' : ''
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            {showChat ? 'Hide Chat' : 'Show Chat'}
          </button>
          
          <button className="btn-secondary flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Settings
          </button>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Sidebar - Prompts and Context */}
        {!showChat || window.innerWidth >= 1024 ? (
          <div className="w-80 border-r border-gray-700 overflow-y-auto">
            {/* Quick Stats */}
            <div className="p-4 border-b border-gray-700">
              <h3 className="font-semibold text-textPrimary mb-3">Today's Overview</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-textSecondary">Pending Tasks</span>
                  <span className="text-warning font-medium">{pendingTasks.length}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-textSecondary">In Progress</span>
                  <span className="text-primary font-medium">{inProgressTasks.length}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-textSecondary">Completed Today</span>
                  <span className="text-success font-medium">{completedToday.length}</span>
                </div>
              </div>
            </div>

            {/* Quick Prompts */}
            <div className="p-4">
              <h3 className="font-semibold text-textPrimary mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                Quick Prompts
              </h3>
              
              <div className="space-y-4">
                {quickPrompts.map((category, categoryIndex) => {
                  const Icon = category.icon
                  return (
                    <div key={categoryIndex}>
                      <h4 className="text-sm font-medium text-textSecondary mb-2 flex items-center gap-2">
                        <Icon className="w-3 h-3" />
                        {category.category}
                      </h4>
                      <div className="space-y-1">
                        {category.prompts.map((prompt, promptIndex) => (
                          <button
                            key={promptIndex}
                            onClick={() => {
                              // This would trigger the prompt in the chat
                              const chatInput = document.querySelector('input[placeholder*="Ask me anything"]') as HTMLInputElement
                              if (chatInput) {
                                chatInput.value = prompt
                                chatInput.focus()
                              }
                            }}
                            className="w-full text-left text-xs p-2 text-textPrimary hover:bg-surface rounded transition-colors"
                          >
                            "{prompt}"
                          </button>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Help */}
            <div className="p-4 border-t border-gray-700">
              <div className="bg-primary/10 border border-primary/20 rounded-lg p-3">
                <h4 className="text-sm font-medium text-primary mb-1 flex items-center gap-1">
                  <HelpCircle className="w-3 h-3" />
                  Tips
                </h4>
                <p className="text-xs text-textSecondary">
                  I can help you create tasks, analyze productivity patterns, suggest schedules, 
                  and answer questions about your work habits. Try asking in natural language!
                </p>
              </div>
            </div>
          </div>
        ) : null}

        {/* Chat Area */}
        {showChat ? (
          <div className="flex-1 flex flex-col">
            <AgentChat className="flex-1" />
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center">
              <div className="w-24 h-24 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-12 h-12 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-textPrimary mb-2">
                Ready to Help
              </h3>
              <p className="text-textSecondary mb-6 max-w-md">
                Click "Show Chat" to start a conversation with your AI agent. I can help with 
                task management, scheduling, productivity analysis, and more.
              </p>
              <button
                onClick={() => setShowChat(true)}
                className="btn-primary flex items-center gap-2 mx-auto"
              >
                <MessageSquare className="w-4 h-4" />
                Start Chatting
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}