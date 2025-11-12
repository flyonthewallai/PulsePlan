import { useRef, useEffect, useState } from 'react'

type TodoTimeFilter = 'all' | 'due_soon'

interface TodoFilterTabsProps {
  timeFilter: TodoTimeFilter
  onFilterChange: (filter: TodoTimeFilter) => void
}

export function TodoFilterTabs({ timeFilter, onFilterChange }: TodoFilterTabsProps) {
  const allRef = useRef<HTMLButtonElement>(null)
  const dueSoonRef = useRef<HTMLButtonElement>(null)

  const [highlightStyle, setHighlightStyle] = useState<{ left: number; width: number }>({ left: 0, width: 0 })

  const tabRefs = {
    all: allRef,
    due_soon: dueSoonRef,
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
        ref={dueSoonRef}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onFilterChange('due_soon')
        }}
        className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
          timeFilter === 'due_soon'
            ? 'text-neutral-900'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        Due Soon
      </button>
    </div>
  )
}

