import React, { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { cn } from '../../lib/utils'
import { typography, components, spacing } from '../../lib/design-tokens'

interface CourseColorPickerProps {
  visible: boolean
  onClose: () => void
  onSelectColor: (color: string) => void
  currentColor: string
  courseName: string
}

// Same colors as RN app - darker, blue-tinted rainbow spectrum
const sleekColors = [
  '#B91C1C', '#DC2626', '#BE185D', '#EC4899',  // Reds & Pinks
  '#D97706', '#F59E0B', '#CA8A04', '#A3A3A3',  // Oranges & Yellows
  '#166534', '#059669', '#0D9488', '#0F766E',  // Greens & Teals
  '#0369A1', '#1E40AF', '#3730A3', '#6B21A8',  // Blues & Purples
]

export function CourseColorPicker({
  visible,
  onClose,
  onSelectColor,
  currentColor,
  courseName
}: CourseColorPickerProps) {
  const [previewColor, setPreviewColor] = useState(currentColor)

  useEffect(() => {
    setPreviewColor(currentColor)
  }, [currentColor, visible])

  if (!visible) return null

  const handleColorSelect = (color: string) => {
    onSelectColor(color)
    onClose()
  }

  const handleColorMouseEnter = (color: string) => {
    setPreviewColor(color)
  }

  const handleColorMouseLeave = () => {
    setPreviewColor(currentColor)
  }

  return (
    <div
      className={components.modal.overlay}
      onClick={onClose}
    >
      <div
        className={cn(components.modal.container, "max-w-sm")}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={components.modal.header}>
          <div className="flex items-center justify-between w-full">
            <div>
              <h3 className={components.modal.title}>Choose Color</h3>
              <p className="text-xs text-gray-400 mt-0.5">{courseName}</p>
            </div>
            <button
              onClick={onClose}
              className={components.modal.closeButton}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Color Grid */}
        <div className={components.modal.content}>
          <div className="grid grid-cols-4 gap-2">
            {sleekColors.map((color) => (
              <button
                key={color}
                className={`
                  aspect-square rounded-xl transition-all duration-200
                  hover:scale-105 active:scale-95
                  ${currentColor === color ? 'ring-2 ring-white ring-offset-1 ring-offset-neutral-800 scale-105' : ''}
                `}
                style={{
                  backgroundColor: color,
                  boxShadow: currentColor === color
                    ? `0 0 12px ${color}60`
                    : '0 2px 4px rgba(0,0,0,0.1)'
                }}
                onClick={() => handleColorSelect(color)}
                onMouseEnter={() => handleColorMouseEnter(color)}
                onMouseLeave={handleColorMouseLeave}
              >
                {currentColor === color && (
                  <div className="w-full h-full flex items-center justify-center">
                    <div className="bg-white/90 rounded-full w-5 h-5 flex items-center justify-center">
                      <span className="text-black text-xs font-semibold">✓</span>
                    </div>
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* Preview */}
          <div className="mt-4">
            <p className={cn(typography.body.small, "font-medium text-gray-400 uppercase tracking-wider mb-2")}>
              Preview
            </p>
            <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-3 flex items-center">
              <div
                className="w-5 h-5 rounded-full mr-3"
                style={{ backgroundColor: previewColor }}
              />
              <span className="text-sm font-semibold text-white">{courseName}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
