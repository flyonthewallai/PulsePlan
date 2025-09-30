import React, { useState } from 'react'
import { BrainCircuit, CheckCircle2, Clock, CheckCheck, Check, BarChart3 } from 'lucide-react'

export function DailySummaryCard() {
  const [showMessage, setShowMessage] = useState(true)

  if (!showMessage) {
    return (
      <div className="mb-5">
        {/* Overview Section Header */}
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
            OVERVIEW
          </span>
          <BarChart3 size={16} className="text-gray-400" />
        </div>
        
        <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
          <div className="flex items-center">
            <div className="flex items-center gap-3">
              <CheckCircle2 size={20} className="text-white opacity-90" />
              <span className="text-sm font-medium text-white">5 Tasks Today</span>
            </div>
          </div>
          <div className="flex items-center mt-3">
            <div className="flex items-center gap-3">
              <Clock size={20} className="text-white opacity-90" />
              <span className="text-sm font-medium text-white">3.5h Est. Time</span>
            </div>
          </div>
          <div className="flex items-center mt-3">
            <div className="flex items-center gap-3">
              <CheckCheck size={20} className="text-white opacity-90" />
              <span className="text-sm font-medium text-white">2 Done</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mb-5">
      <div className="flex items-start gap-3 mb-6">
        <div className="w-8 h-8 bg-gray-700 rounded-lg flex items-center justify-center">
          <BrainCircuit size={24} className="text-white" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <span className="font-bold text-base text-white">Pulse</span>
            <button 
              className="p-1 -mr-1"
              onClick={() => setShowMessage(false)}
            >
              <Check size={18} className="text-gray-400" />
            </button>
          </div>
          <p className="text-lg leading-relaxed text-white">
            Today you have 3 priority tasks focused on Computer Science and Mathematics. 
            Your most important task is the "Algorithm Analysis" due at 2:00 PM. 
            I suggest starting with this as it requires focused concentration.
          </p>
        </div>
      </div>

      {/* Overview Section Header */}
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
          OVERVIEW
        </span>
        <BarChart3 size={16} className="text-gray-400" />
      </div>

      <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4">
        <div className="flex items-center">
          <div className="flex items-center gap-3">
            <CheckCircle2 size={20} className="text-white opacity-90" />
            <span className="text-sm font-medium text-white">5 Tasks Today</span>
          </div>
        </div>
        <div className="flex items-center mt-3">
          <div className="flex items-center gap-3">
            <Clock size={20} className="text-white opacity-90" />
            <span className="text-sm font-medium text-white">3.5h Est. Time</span>
          </div>
        </div>
        <div className="flex items-center mt-3">
          <div className="flex items-center gap-3">
            <CheckCheck size={20} className="text-white opacity-90" />
            <span className="text-sm font-medium text-white">2 Done</span>
          </div>
        </div>
      </div>
    </div>
  )
}
