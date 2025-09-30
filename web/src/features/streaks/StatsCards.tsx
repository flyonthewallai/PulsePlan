import React from 'react'
import { Flame, Target, TrendingUp, Clock, Calendar, CheckCircle2 } from 'lucide-react'
import { format, subDays, isAfter, isBefore, parseISO } from 'date-fns'
import type { Task } from '../../types'

interface StatsCardsProps {
  tasks: Task[]
}

export function StatsCards({ tasks }: StatsCardsProps) {
  // Calculate streak data
  const calculateCurrentStreak = () => {
    const sortedDays = []
    const today = new Date()
    
    // Check each day going backwards from today
    for (let i = 0; i < 365; i++) {
      const checkDate = subDays(today, i)
      const dayTasks = tasks.filter(task => {
        const taskDate = parseISO(task.due_date)
        return format(taskDate, 'yyyy-MM-dd') === format(checkDate, 'yyyy-MM-dd')
      })
      
      const completedTasks = dayTasks.filter(task => task.status === 'completed')
      const hasActivity = dayTasks.length > 0
      const hasCompletion = completedTasks.length > 0
      
      if (hasActivity && hasCompletion) {
        sortedDays.push(checkDate)
      } else if (hasActivity) {
        // Had tasks but didn't complete any - breaks streak
        break
      }
      // Days with no tasks don't break streak, just don't count
    }
    
    return sortedDays.length
  }

  const calculateLongestStreak = () => {
    // This is a simplified version - in production you'd want to store this data
    return Math.max(calculateCurrentStreak(), tasks.filter(t => t.status === 'completed').length / 7)
  }

  const calculateWeeklyStats = () => {
    const weekAgo = subDays(new Date(), 7)
    const weekTasks = tasks.filter(task => 
      isAfter(parseISO(task.due_date), weekAgo)
    )
    
    const completed = weekTasks.filter(task => task.status === 'completed').length
    const total = weekTasks.length
    const rate = total > 0 ? (completed / total) * 100 : 0
    
    return { completed, total, rate }
  }

  const calculateMonthlyStats = () => {
    const monthAgo = subDays(new Date(), 30)
    const monthTasks = tasks.filter(task => 
      isAfter(parseISO(task.due_date), monthAgo)
    )
    
    const completed = monthTasks.filter(task => task.status === 'completed').length
    const total = monthTasks.length
    const rate = total > 0 ? (completed / total) * 100 : 0
    
    return { completed, total, rate }
  }

  const calculateAverageTaskTime = () => {
    const completedTasks = tasks.filter(task => task.status === 'completed')
    if (completedTasks.length === 0) return 0
    
    const totalMinutes = completedTasks.reduce((sum, task) => 
      sum + (task.estimated_minutes || 60), 0
    )
    
    return Math.round(totalMinutes / completedTasks.length)
  }

  const currentStreak = calculateCurrentStreak()
  const longestStreak = calculateLongestStreak()
  const weeklyStats = calculateWeeklyStats()
  const monthlyStats = calculateMonthlyStats()
  const avgTaskTime = calculateAverageTaskTime()
  const totalCompleted = tasks.filter(task => task.status === 'completed').length

  const stats = [
    {
      title: 'Current Streak',
      value: currentStreak,
      unit: currentStreak === 1 ? 'day' : 'days',
      icon: Flame,
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/20',
      description: 'Consecutive days with completed tasks'
    },
    {
      title: 'Longest Streak',
      value: Math.round(longestStreak),
      unit: 'days',
      icon: Target,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/20',
      description: 'Your personal best streak'
    },
    {
      title: 'Weekly Rate',
      value: Math.round(weeklyStats.rate),
      unit: '%',
      icon: TrendingUp,
      color: 'text-success',
      bgColor: 'bg-success/20',
      description: `${weeklyStats.completed}/${weeklyStats.total} tasks this week`
    },
    {
      title: 'Monthly Rate',
      value: Math.round(monthlyStats.rate),
      unit: '%',
      icon: Calendar,
      color: 'text-primary',
      bgColor: 'bg-primary/20',
      description: `${monthlyStats.completed}/${monthlyStats.total} tasks this month`
    },
    {
      title: 'Avg Task Time',
      value: avgTaskTime,
      unit: 'min',
      icon: Clock,
      color: 'text-warning',
      bgColor: 'bg-warning/20',
      description: 'Average estimated task duration'
    },
    {
      title: 'Total Completed',
      value: totalCompleted,
      unit: 'tasks',
      icon: CheckCircle2,
      color: 'text-success',
      bgColor: 'bg-success/20',
      description: 'All-time completed tasks'
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {stats.map((stat, index) => {
        const Icon = stat.icon
        return (
          <div key={index} className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <Icon className={`w-6 h-6 ${stat.color}`} />
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-textPrimary">
                  {stat.value}
                  <span className="text-sm font-normal text-textSecondary ml-1">
                    {stat.unit}
                  </span>
                </div>
              </div>
            </div>
            
            <h3 className="font-semibold text-textPrimary mb-2">{stat.title}</h3>
            <p className="text-sm text-textSecondary">{stat.description}</p>
            
            {/* Progress indicator for percentage stats */}
            {stat.unit === '%' && (
              <div className="mt-3">
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      stat.value >= 80 
                        ? 'bg-success' 
                        : stat.value >= 60 
                        ? 'bg-warning' 
                        : 'bg-error'
                    }`}
                    style={{ width: `${Math.max(stat.value, 2)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}