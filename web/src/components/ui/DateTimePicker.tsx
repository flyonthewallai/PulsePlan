import React, { useState, useRef, useEffect } from 'react'
import { Calendar, Clock, ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '../../lib/utils'
import { format, addMonths, subMonths, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, isToday, parseISO } from 'date-fns'

interface DateTimePickerProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  placeholder?: string
}

export function DateTimePicker({ value, onChange, disabled, placeholder = "Select date and time" }: DateTimePickerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selectedDate, setSelectedDate] = useState<Date | null>(value ? parseISO(value) : null)
  const [timeValue, setTimeValue] = useState(
    value ? format(parseISO(value), 'HH:mm') : '12:00'
  )
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (value) {
      const date = parseISO(value)
      setSelectedDate(date)
      setTimeValue(format(date, 'HH:mm'))
      setCurrentMonth(date)
    }
  }, [value])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const daysInMonth = eachDayOfInterval({ start: monthStart, end: monthEnd })

  // Get the day of week for the first day (0 = Sunday, 6 = Saturday)
  const firstDayOfWeek = monthStart.getDay()

  // Create array of null values for empty cells before month starts
  const emptyDays = Array(firstDayOfWeek).fill(null)

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date)
    const [hours, minutes] = timeValue.split(':')
    const newDate = new Date(date)
    newDate.setHours(parseInt(hours), parseInt(minutes))
    onChange(format(newDate, "yyyy-MM-dd'T'HH:mm"))
  }

  const handleTimeChange = (time: string) => {
    setTimeValue(time)
    if (selectedDate) {
      const [hours, minutes] = time.split(':')
      const newDate = new Date(selectedDate)
      newDate.setHours(parseInt(hours), parseInt(minutes))
      onChange(format(newDate, "yyyy-MM-dd'T'HH:mm"))
    }
  }

  const displayValue = selectedDate
    ? `${format(selectedDate, 'MMM d, yyyy')} at ${timeValue}`
    : placeholder

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          "w-full bg-neutral-800/40 border border-gray-700/50 rounded-lg px-3 py-2.5 text-left focus:outline-none focus:border-gray-600 transition-colors text-sm flex items-center justify-between",
          disabled && "opacity-50 cursor-not-allowed",
          selectedDate ? "text-white" : "text-gray-500"
        )}
      >
        <span className="truncate">{displayValue}</span>
        <Calendar className="w-4 h-4 text-gray-400 flex-shrink-0 ml-2" />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-2 bg-neutral-800 border border-gray-700/50 rounded-xl shadow-2xl overflow-hidden" style={{ width: '320px' }}>
          {/* Calendar Header */}
          <div className="flex items-center justify-between p-3 border-b border-gray-700/50">
            <button
              type="button"
              onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
              className="p-1.5 hover:bg-neutral-700/50 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-4 h-4 text-gray-400" />
            </button>
            <span className="text-white font-semibold text-sm">
              {format(currentMonth, 'MMMM yyyy')}
            </span>
            <button
              type="button"
              onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
              className="p-1.5 hover:bg-neutral-700/50 rounded-lg transition-colors"
            >
              <ChevronRight className="w-4 h-4 text-gray-400" />
            </button>
          </div>

          {/* Calendar Grid */}
          <div className="p-3">
            {/* Day headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
                <div key={day} className="text-center text-xs font-medium text-gray-500 py-1">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar days */}
            <div className="grid grid-cols-7 gap-1">
              {emptyDays.map((_, index) => (
                <div key={`empty-${index}`} className="aspect-square" />
              ))}
              {daysInMonth.map((day) => {
                const isSelected = selectedDate && isSameDay(day, selectedDate)
                const isCurrentDay = isToday(day)
                const isCurrentMonth = isSameMonth(day, currentMonth)

                return (
                  <button
                    key={day.toISOString()}
                    type="button"
                    onClick={() => handleDateSelect(day)}
                    className={cn(
                      "aspect-square rounded-lg text-sm font-medium transition-all",
                      isSelected && "bg-blue-500 text-white",
                      !isSelected && isCurrentDay && "border border-blue-500 text-blue-400",
                      !isSelected && !isCurrentDay && isCurrentMonth && "text-white hover:bg-neutral-700/50",
                      !isSelected && !isCurrentDay && !isCurrentMonth && "text-gray-600"
                    )}
                  >
                    {format(day, 'd')}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Time Picker */}
          <div className="border-t border-gray-700/50 p-3">
            <label className="flex items-center gap-2 text-white text-xs font-medium mb-2">
              <Clock className="w-3.5 h-3.5" />
              Time
            </label>
            <input
              type="time"
              value={timeValue}
              onChange={(e) => handleTimeChange(e.target.value)}
              className="w-full bg-neutral-700/50 border border-gray-600/50 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors [color-scheme:dark]"
            />
          </div>

          {/* Action Buttons */}
          <div className="border-t border-gray-700/50 p-3 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="px-3 py-1.5 text-gray-400 hover:text-white text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => {
                if (selectedDate) {
                  const [hours, minutes] = timeValue.split(':')
                  const newDate = new Date(selectedDate)
                  newDate.setHours(parseInt(hours), parseInt(minutes))
                  onChange(format(newDate, "yyyy-MM-dd'T'HH:mm"))
                }
                setIsOpen(false)
              }}
              className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
