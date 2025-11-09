import { useState } from 'react'
import { X, Sparkles, Loader2 } from 'lucide-react'
import { cn } from '../lib/utils'
import { typography, components, spacing } from '../lib/design-tokens'

interface AddHobbyPromptProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (description: string) => void
  isLoading?: boolean
}

const examplePrompts = [
  "I like to go to the gym in the morning, Monday-Friday, usually 45-60 minutes",
  "I play guitar for about an hour in the evening, 3-4 times a week",
  "I enjoy photography on weekends, usually afternoon for 1-2 hours when weather is good",
  "I read before bed every night for 30-45 minutes",
  "I go running in the morning on weekdays, around 30 minutes"
]

export function AddHobbyPrompt({ isOpen, onClose, onSubmit, isLoading }: AddHobbyPromptProps) {
  const [description, setDescription] = useState('')
  const [showExamples, setShowExamples] = useState(false)

  const handleSubmit = () => {
    if (description.trim()) {
      onSubmit(description.trim())
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleExampleClick = (example: string) => {
    setDescription(example)
    setShowExamples(false)
  }

  if (!isOpen) return null

  return (
    <div className={components.modal.overlay}>
      <div className={cn(components.modal.container, "max-w-lg")}>
        {/* Header */}
        <div className={components.modal.header}>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-blue-400" />
              <h3 className={components.modal.title}>Add a new hobby</h3>
            </div>
            <button
              onClick={onClose}
              className={components.modal.closeButton}
              disabled={isLoading}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className={cn(components.modal.content, spacing.stack.md)}>
          <p className="text-gray-400 text-sm">
            Tell PulsePlan when and how you enjoy it — be as natural as you like.
          </p>

          {/* Input */}
          <div className="relative">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="I usually go to the gym in the morning, 5 days a week..."
              disabled={isLoading}
              className={cn(
                components.textarea.base,
                "w-full min-h-[100px] resize-y",
                isLoading && "opacity-50 cursor-not-allowed"
              )}
              autoFocus
            />
            <div className="absolute bottom-2 right-2 text-xs text-gray-500">
              {description.length}/500
            </div>
          </div>

          {/* Examples toggle */}
          <button
            onClick={() => setShowExamples(!showExamples)}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
            disabled={isLoading}
          >
            {showExamples ? 'Hide examples' : 'Show me some examples'}
          </button>

          {/* Examples dropdown */}
          {showExamples && (
            <div className="space-y-2">
              <p className="text-xs text-gray-500 font-medium">Example prompts:</p>
              {examplePrompts.map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => handleExampleClick(example)}
                  className="w-full text-left px-3 py-2 bg-neutral-800/40 hover:bg-neutral-800/60 border border-gray-700/40 rounded-lg text-xs text-gray-300 transition-colors"
                  disabled={isLoading}
                >
                  {example}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={components.modal.footer}>
          <button
            onClick={onClose}
            disabled={isLoading}
            className={cn(
              components.button.base,
              components.button.secondary,
              isLoading && "opacity-50 cursor-not-allowed"
            )}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!description.trim() || isLoading}
            className={cn(
              components.button.base,
              components.button.primary,
              "flex items-center gap-2",
              (!description.trim() || isLoading) && "opacity-50 cursor-not-allowed"
            )}
          >
            {isLoading ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Analyzing...
              </>
            ) : (
              'Continue'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
