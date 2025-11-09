import { X, Users, ExternalLink } from 'lucide-react'
import { cn } from '../lib/utils'
import { typography, colors, spacing, components, cn as cnTokens } from '../lib/design-tokens'

interface AmbassadorModalProps {
  isOpen: boolean
  onClose: () => void
}

const AMBASSADOR_URL = 'https://www.notion.so/connergroth/2036b20844a880f7a065cc060a0014e3?pvs=106'

export function AmbassadorModal({ isOpen, onClose }: AmbassadorModalProps) {
  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 transition-all duration-300"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className={cn(
        'bg-[#121212] border border-gray-700/50 rounded-2xl w-full max-w-md transition-all duration-300',
        isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
      )}>
        {/* Header */}
        <div className={cn(spacing.modal.header, 'flex items-center justify-between border-b border-gray-700/30')}>
          <h2 className={cn(typography.sectionTitle, colors.text.primary)}>Become an Ambassador</h2>
          <button
            onClick={onClose}
            className={components.modal.closeButton}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className={spacing.modal.content}>
          <div className="mb-4">
            <p className={cn(typography.body.default, colors.text.secondary, 'mb-3')}>
              Join our ambassador program and help grow PulsePlan while earning rewards!
            </p>
            <div className={cn(
              'bg-blue-500/10 border border-blue-500/30 rounded-lg p-3',
              spacing.stack.xs
            )}>
              <div className="flex items-start gap-2">
                <Users size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className={cn(typography.body.small, colors.text.primary, 'font-medium')}>
                    What you get:
                  </p>
                  <p className={cn(typography.body.small, colors.text.secondary)}>
                    Exclusive rewards, early access, and more
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div>
            <a
              href={AMBASSADOR_URL}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(
                components.button.base,
                components.button.primary,
                'w-full flex items-center justify-center gap-2'
              )}
            >
              <span>Learn More</span>
              <ExternalLink size={14} />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}



