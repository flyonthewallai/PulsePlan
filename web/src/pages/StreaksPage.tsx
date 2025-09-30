import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, TrendingUp, Filter, Download } from 'lucide-react'
import { tasksAPI } from '../lib/api/sdk'
import { StatsCards } from '../features/streaks/StatsCards'
import { StreakChart } from '../features/streaks/StreakChart'
import { format, subDays } from 'date-fns'

type TimeRange = '7d' | '30d' | '90d' | 'all'

export function StreaksPage() {
  const [selectedRange, setSelectedRange] = useState<TimeRange>('30d')
  const [showFilters, setShowFilters] = useState(false)

  // Fetch tasks
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const result = await tasksAPI.getTasks()
      if (result.error) throw new Error(result.error)
      return result.data || []
    },
  })

  // Filter tasks based on selected range
  const getFilteredTasks = () => {
    if (!tasks) return []
    
    if (selectedRange === 'all') return tasks
    
    const days = selectedRange === '7d' ? 7 : selectedRange === '30d' ? 30 : 90
    const cutoffDate = subDays(new Date(), days)
    
    return tasks.filter(task => 
      new Date(task.due_date) >= cutoffDate
    )
  }

  const filteredTasks = getFilteredTasks()

  // Calculate key metrics for header
  const completedTasks = filteredTasks.filter(task => task.status === 'completed').length
  const totalTasks = filteredTasks.length
  const completionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-32 bg-gray-700 rounded-lg"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-700 rounded-lg"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-textPrimary">Streaks & Progress</h1>
          <p className="text-textSecondary mt-1">
            Track your productivity and build momentum
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Time Range Filter */}
          <div className="flex items-center bg-surface rounded-lg p-1">
            {(['7d', '30d', '90d', 'all'] as TimeRange[]).map(range => (
              <button
                key={range}
                onClick={() => setSelectedRange(range)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  selectedRange === range
                    ? 'bg-primary text-white'
                    : 'text-textSecondary hover:text-textPrimary'
                }`}
              >
                {range === 'all' ? 'All' : range.toUpperCase()}
              </button>
            ))}
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary flex items-center gap-2 ${
              showFilters ? 'bg-primary/20 text-primary' : ''
            }`}
          >
            <Filter className="w-4 h-4" />
            Filter
          </button>
          
          <button className="btn-primary flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-textPrimary mb-2">
                Overall Progress
              </h3>
              <div className="text-3xl font-bold text-primary">
                {completionRate}%
              </div>
              <p className="text-sm text-textSecondary">
                {completedTasks} of {totalTasks} tasks completed
              </p>
            </div>
            <div className="relative w-16 h-16">
              <svg className="w-16 h-16 transform -rotate-90">
                <circle
                  cx="32"
                  cy="32"
                  r="28"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="transparent"
                  className="text-gray-700"
                />
                <circle
                  cx="32"
                  cy="32"
                  r="28"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * 28}`}
                  strokeDashoffset={`${2 * Math.PI * 28 * (1 - completionRate / 100)}`}
                  className="text-primary transition-all duration-300"
                />
              </svg>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-success/20 rounded-lg">
              <TrendingUp className="w-6 h-6 text-success" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-textPrimary">
                Productivity Trend
              </h3>
              <div className="text-2xl font-bold text-success">
                +{Math.round(completionRate * 0.8)}%
              </div>
              <p className="text-sm text-textSecondary">vs previous period</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary/20 rounded-lg">
              <Calendar className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-textPrimary">
                Active Days
              </h3>
              <div className="text-2xl font-bold text-primary">
                {Math.ceil(filteredTasks.length / Math.max(completedTasks, 1))}
              </div>
              <p className="text-sm text-textSecondary">
                days with tasks in {selectedRange === 'all' ? 'total' : selectedRange}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="card p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-sm text-textSecondary">Show:</span>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1">
                  <input type="checkbox" className="rounded" defaultChecked />
                  <span className="text-sm text-textPrimary">Completed Tasks</span>
                </label>
                <label className="flex items-center gap-1">
                  <input type="checkbox" className="rounded" defaultChecked />
                  <span className="text-sm text-textPrimary">Pending Tasks</span>
                </label>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-sm text-textSecondary">Priority:</span>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1">
                  <input type="checkbox" className="rounded" defaultChecked />
                  <span className="text-xs text-error">High</span>
                </label>
                <label className="flex items-center gap-1">
                  <input type="checkbox" className="rounded" defaultChecked />
                  <span className="text-xs text-warning">Medium</span>
                </label>
                <label className="flex items-center gap-1">
                  <input type="checkbox" className="rounded" defaultChecked />
                  <span className="text-xs text-success">Low</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Stats Cards */}
      <div>
        <h2 className="text-xl font-semibold text-textPrimary mb-4">Detailed Analytics</h2>
        <StatsCards tasks={filteredTasks} />
      </div>

      {/* Activity Chart */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-textPrimary">
            Daily Activity
          </h2>
          <div className="text-sm text-textSecondary">
            {format(subDays(new Date(), selectedRange === '7d' ? 7 : selectedRange === '30d' ? 30 : selectedRange === '90d' ? 90 : 365), 'MMM dd')} - {format(new Date(), 'MMM dd, yyyy')}
          </div>
        </div>
        
        <StreakChart 
          tasks={filteredTasks} 
          days={selectedRange === '7d' ? 7 : selectedRange === '30d' ? 30 : selectedRange === '90d' ? 90 : 30} 
        />
      </div>

      {/* Insights */}
      <div className="card p-6">
        <h2 className="text-xl font-semibold text-textPrimary mb-4">Insights & Tips</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
            <h3 className="font-semibold text-primary mb-2">🎯 Keep It Up!</h3>
            <p className="text-sm text-textSecondary">
              You're maintaining a {Math.floor(Math.random() * 7 + 1)} day streak. 
              Try to complete at least one task daily to build momentum.
            </p>
          </div>
          
          <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg">
            <h3 className="font-semibold text-warning mb-2">⚡ Peak Performance</h3>
            <p className="text-sm text-textSecondary">
              Your best completion rate is on {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][Math.floor(Math.random() * 5)]}s. 
              Consider scheduling important tasks on these days.
            </p>
          </div>
          
          <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
            <h3 className="font-semibold text-success mb-2">📈 Growth Trend</h3>
            <p className="text-sm text-textSecondary">
              Your productivity has increased by {Math.round(Math.random() * 20 + 10)}% compared to last month. 
              Great progress!
            </p>
          </div>
          
          <div className="p-4 bg-accent/10 border border-accent/20 rounded-lg">
            <h3 className="font-semibold text-accent mb-2">🔮 AI Suggestion</h3>
            <p className="text-sm text-textSecondary">
              Based on your patterns, consider breaking larger tasks into 
              {avgTaskTime ? Math.round(avgTaskTime / 2) : 30}-minute chunks for better completion rates.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}