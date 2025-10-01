import React, { useState, useEffect } from 'react'
import { X } from 'lucide-react'

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
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-neutral-800 border border-gray-700 rounded-2xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-700">
          <div>
            <h3 className="text-lg font-semibold text-white">Choose Color</h3>
            <p className="text-sm text-gray-400 mt-0.5">{courseName}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-neutral-700 rounded-lg transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        {/* Color Grid */}
        <div className="p-6">
          <div className="grid grid-cols-4 gap-4">
            {sleekColors.map((color) => (
              <button
                key={color}
                className={`
                  aspect-square rounded-2xl transition-all duration-200
                  hover:scale-105 active:scale-95
                  ${currentColor === color ? 'ring-3 ring-white ring-offset-2 ring-offset-neutral-800 scale-105' : ''}
                `}
                style={{
                  backgroundColor: color,
                  boxShadow: currentColor === color
                    ? `0 0 20px ${color}60`
                    : '0 2px 4px rgba(0,0,0,0.1)'
                }}
                onClick={() => handleColorSelect(color)}
                onMouseEnter={() => handleColorMouseEnter(color)}
                onMouseLeave={handleColorMouseLeave}
              >
                {currentColor === color && (
                  <div className="w-full h-full flex items-center justify-center">
                    <div className="bg-white/90 rounded-full w-6 h-6 flex items-center justify-center">
                      <span className="text-black text-sm font-semibold">✓</span>
                    </div>
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* Preview */}
          <div className="mt-6">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
              Preview
            </p>
            <div className="bg-neutral-700/50 rounded-xl p-4 flex items-center">
              <div
                className="w-6 h-6 rounded-full mr-4"
                style={{ backgroundColor: previewColor }}
              />
              <span className="text-base font-semibold text-white">{courseName}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
