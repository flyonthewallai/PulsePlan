import { useState } from 'react'
import { X, Gift, Mail, Check } from 'lucide-react'
import { cn } from '../lib/utils'
import { typography, colors, spacing, components, cn as cnTokens } from '../lib/design-tokens'
import { referralApi } from '../lib/api/sdk'

interface ReferralModalProps {
  isOpen: boolean
  onClose: () => void
}

export function ReferralModal({ isOpen, onClose }: ReferralModalProps) {
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email.trim() || !email.includes('@')) {
      setError('Please enter a valid email address')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      await referralApi.sendInvite(email.trim())
      setIsSuccess(true)
      setEmail('')
      
      // Reset success state after 3 seconds
      setTimeout(() => {
        setIsSuccess(false)
        onClose()
      }, 3000)
    } catch (err: any) {
      setError(err.message || 'Failed to send referral email. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

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
          <h2 className={cn(typography.sectionTitle, colors.text.primary)}>Share PulsePlan</h2>
          <button
            onClick={onClose}
            className={components.modal.closeButton}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className={spacing.modal.content}>
          {isSuccess ? (
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="p-3 rounded-full bg-green-500/10">
                <Check size={24} className="text-green-400" />
              </div>
              <div>
                <h3 className={cn(typography.subsectionTitle, colors.text.primary, 'mb-2')}>
                  Invitation sent!
                </h3>
                <p className={cn(typography.body.default, colors.text.secondary)}>
                  Your friend will receive an email with a special signup reward.
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className="mb-4">
                <p className={cn(typography.body.default, colors.text.secondary, 'mb-3')}>
                  Invite a friend to PulsePlan and you'll both get 1 month of Premium free when they sign up!
                </p>
                <div className={cn(
                  'bg-blue-500/10 border border-blue-500/30 rounded-lg p-3',
                  spacing.stack.xs
                )}>
                  <div className="flex items-start gap-2">
                    <Gift size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className={cn(typography.body.small, colors.text.primary, 'font-medium')}>
                        Both of you get:
                      </p>
                      <p className={cn(typography.body.small, colors.text.secondary)}>
                        1 month of Premium free
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <form onSubmit={handleSubmit} className={spacing.stack.md}>
                <div>
                  <label className={cn(typography.input.label, colors.text.secondary, 'mb-2 block')}>
                    Friend's email
                  </label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value)
                        setError(null)
                      }}
                      placeholder="friend@example.com"
                      className={cn(
                        components.input.base,
                        'w-full pl-10',
                        error && components.input.error
                      )}
                      disabled={isSubmitting}
                    />
                  </div>
                  {error && (
                    <p className={cn(typography.input.helper, colors.text.error, 'mt-1')}>
                      {error}
                    </p>
                  )}
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={isSubmitting || !email.trim()}
                    className={cn(
                      components.button.base,
                      components.button.primary,
                      'w-full flex items-center justify-center gap-2',
                      (isSubmitting || !email.trim()) && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                        <span>Sending...</span>
                      </>
                    ) : (
                      <>
                        <Mail size={14} />
                        <span>Send Invitation</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

