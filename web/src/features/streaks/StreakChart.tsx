import React from 'react'
import { format, subDays, startOfDay, endOfDay, isToday, parseISO } from 'date-fns'
import type { Task } from '../../types'

interface StreakChartProps {
  tasks: Task[]
  days?: number
}

export function StreakChart({ tasks, days = 30 }: StreakChartProps) {
  // Generate array of last N days
  const chartDays = Array.from({ length: days }, (_, i) => {
    const date = subDays(new Date(), days - 1 - i)
    return startOfDay(date)
  })

  // Calculate completion for each day
  const dayData = chartDays.map(day => {
    const dayStart = startOfDay(day)
    const dayEnd = endOfDay(day)
    
    const dayTasks = tasks.filter(task => {
      const taskDate = parseISO(task.due_date)
      return taskDate >= dayStart && taskDate <= dayEnd
    })
    
    const completedTasks = dayTasks.filter(task => task.status === 'completed')
    const completionRate = dayTasks.length > 0 ? (completedTasks.length / dayTasks.length) * 100 : 0
    
    return {
      date: day,
      totalTasks: dayTasks.length,
      completedTasks: completedTasks.length,
      completionRate,
      isToday: isToday(day),
    }
  })

  const maxTasks = Math.max(...dayData.map(d => d.totalTasks), 1)

  return (
    <div className="w-full">
      <div className="flex items-end justify-between h-32 gap-1">
        {dayData.map((day, index) => {
          const height = day.totalTasks > 0 ? (day.totalTasks / maxTasks) * 100 : 2
          const completedHeight = day.completedTasks > 0 ? (day.completedTasks / maxTasks) * 100 : 0
          
          return (
            <div key={index} className="flex flex-col items-center flex-1 group">
              {/* Bar container */}
              <div className="relative h-24 w-full max-w-6 flex items-end">
                {/* Background bar */}
                <div
                  className="w-full bg-gray-700 rounded-sm relative overflow-hidden"
                  style={{ height: `${Math.max(height, 2)}%` }}
                >
                  {/* Completed portion */}
                  {completedHeight > 0 && (
                    <div
                      className="absolute bottom-0 left-0 w-full bg-success rounded-sm"
                      style={{ height: `${(completedHeight / height) * 100}%` }}
                    />
                  )}
                </div>
                
                {/* Today indicator */}
                {day.isToday && (
                  <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-primary rounded-full" />
                )}
              </div>
              
              {/* Date label */}
              <div className="mt-2 text-xs text-textSecondary text-center">
                {format(day.date, 'dd')}
              </div>
              
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-card rounded shadow-lg border border-gray-600 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                <div className="text-xs text-textPrimary">
                  {format(day.date, 'MMM dd')}
                </div>
                <div className="text-xs text-textSecondary">
                  {day.completedTasks}/{day.totalTasks} completed
                </div>
                {day.totalTasks > 0 && (
                  <div className="text-xs text-success">
                    {Math.round(day.completionRate)}% rate
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
      
      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-gray-700 rounded-sm" />
          <span className="text-textSecondary">Total Tasks</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-success rounded-sm" />
          <span className="text-textSecondary">Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-primary rounded-full" />
          <span className="text-textSecondary">Today</span>
        </div>
      </div>
    </div>
  )
}