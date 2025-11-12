import { useRef, useEffect, useState } from 'react'

type TimeFilter = 'week' | 'month' | 'all' | 'past'

interface TaskFilterTabsProps {
  timeFilter: TimeFilter
  onFilterChange: (filter: TimeFilter) => void
}

export function TaskFilterTabs({ timeFilter, onFilterChange }: TaskFilterTabsProps) {
  const weekRef = useRef<HTMLButtonElement>(null)
  const monthRef = useRef<HTMLButtonElement>(null)
  const pastRef = useRef<HTMLButtonElement>(null)
  const allRef = useRef<HTMLButtonElement>(null)

  const [highlightStyle, setHighlightStyle] = useState<{ left: number; width: number }>({ left: 0, width: 0 })

  const tabRefs = {
    week: weekRef,
    month: monthRef,
    past: pastRef,
    all: allRef,
  }

  useEffect(() => {
    const activeTabRef = tabRefs[timeFilter]
    if (activeTabRef.current) {
      setHighlightStyle({
        left: activeTabRef.current.offsetLeft,
        width: activeTabRef.current.offsetWidth,
      })
    }
  }, [timeFilter])

  return (
    <div className="relative flex rounded-lg p-1 bg-neutral-900/50 border border-gray-700/50">
      <div
        className="absolute top-1 bottom-1 bg-white rounded-md transition-all duration-300 ease-out shadow-sm"
        style={highlightStyle}
      />
      <button
        ref={weekRef}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onFilterChange('week')
        }}
        className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
          timeFilter === 'week'
            ? 'text-neutral-900'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        Week
      </button>
      <button
        ref={monthRef}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onFilterChange('month')
        }}
        className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
          timeFilter === 'month'
            ? 'text-neutral-900'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        Month
      </button>
      <button
        ref={allRef}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onFilterChange('all')
        }}
        className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
          timeFilter === 'all'
            ? 'text-neutral-900'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        All
      </button>
      <button
        ref={pastRef}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onFilterChange('past')
        }}
        className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
          timeFilter === 'past'
            ? 'text-neutral-900'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        Past
      </button>
    </div>
  )
}

