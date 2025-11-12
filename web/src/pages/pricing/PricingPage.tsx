import { useNavigate } from 'react-router-dom'
import { Sparkles, Check, X, ArrowLeft } from 'lucide-react'
import { components, typography, spacing, colors, layout, cn as cnTokens } from '@/lib/design-tokens'
import { useProfile } from '@/hooks/profile'

export function PricingPage() {
  const navigate = useNavigate()
  const { data: profile } = useProfile()
  const isPremium = profile?.subscription_status === 'premium'

  const features = {
    free: [
      { text: 'Basic task + deadline management', included: true },
      { text: '1 schedule per week', included: true },
      { text: 'Google/Apple Calendar integration', included: true },
      { text: 'Limited agent access', included: true },
      { text: 'Limited canvas sync (1 course)', included: true },
      { text: 'Limited task storage', included: true },
      { text: 'AI task breakdown & automation', included: false },
      { text: 'Smart auto-scheduling & rescheduling', included: false },
      { text: 'Unlimited Canvas sync (all courses)', included: false },
      { text: 'Long term memory of you', included: false },
      { text: 'Auto-draft & summarize emails', included: false },
      { text: 'Daily AI morning briefings', included: false },
      { text: 'Custom AI preferences', included: false },
      { text: 'Priority support & early access', included: false },
    ],
    premium: [
      { text: 'Basic task + deadline management', included: true },
      { text: 'Unlimited schedules per week', included: true },
      { text: 'Google/Apple Calendar integration', included: true },
      { text: 'Unlimited agent access', included: true },
      { text: 'Unlimited canvas sync (all courses)', included: true },
      { text: 'Unlimited task storage', included: true },
      { text: 'AI task breakdown & automation', included: true },
      { text: 'Smart auto-scheduling & rescheduling', included: true },
      { text: 'Unlimited Canvas sync (all courses)', included: true },
      { text: 'Long term memory of you', included: true },
      { text: 'Auto-draft & summarize emails', included: true },
      { text: 'Daily AI morning briefings', included: true },
      { text: 'Custom AI preferences', included: true },
      { text: 'Priority support & early access', included: true },
    ],
  }

  return (
    <div className="min-h-screen bg-[#0f0f0f]">
      {/* Back Button */}
      <div className="absolute top-4 left-4 z-10">
        <button
          onClick={() => navigate('/')}
          className={cnTokens(
            components.iconButton.small,
            "text-gray-400 hover:text-white"
          )}
          aria-label="Back to Home"
        >
          <ArrowLeft size={18} />
        </button>
      </div>

      <div className="w-full max-w-4xl mx-auto px-6 pt-24 pb-6">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className={cnTokens(typography.pageTitle, colors.text.primary, "mb-4")}>Upgrade your plan</h1>
          <p className={cnTokens(typography.body.large, colors.text.secondary, "max-w-2xl mx-auto")}>
            Unlock advanced AI scheduling, unlimited integrations, and powerful productivity features
          </p>
        </div>

        {/* Pricing Cards */}
        <div className={cnTokens(layout.grid.cols2, "gap-6 mb-12 max-w-5xl mx-auto")}>
          {/* Free Plan */}
          <div className={cnTokens(components.card.base, "flex flex-col")}>
            <div className="mb-6">
              <h2 className={cnTokens(typography.sectionTitle, colors.text.primary, "mb-2")}>Free</h2>
              <div className="flex items-baseline gap-2 mb-4">
                <span className={cnTokens(typography.pageTitle, colors.text.primary)}>$0</span>
                <span className={cnTokens(typography.body.small, colors.text.secondary)}>/month</span>
              </div>
              <p className={cnTokens(typography.body.small, colors.text.secondary)}>
                Perfect for getting started with task management
              </p>
            </div>

            <div className={cnTokens(spacing.stack.md, "flex-1 mb-6")}>
              {features.free.map((feature, index) => (
                <div key={index} className="flex items-start gap-3">
                  {feature.included ? (
                    <Check size={18} className={cnTokens(colors.text.success, "mt-0.5 flex-shrink-0")} />
                  ) : (
                    <X size={18} className={cnTokens(colors.text.muted, "mt-0.5 flex-shrink-0")} />
                  )}
                  <span className={cnTokens(
                    typography.body.default,
                    feature.included ? colors.text.primary : colors.text.muted
                  )}>
                    {feature.text}
                  </span>
                </div>
              ))}
            </div>

            <button
              onClick={() => navigate('/')}
              className={cnTokens(components.button.base, components.button.secondary, "w-full")}
            >
              {isPremium ? 'Back to Home' : 'Continue free'}
            </button>
          </div>

          {/* Premium Plan */}
          <div className={cnTokens(components.card.base, "flex flex-col border-2 border-blue-500/30 relative")}>
            {isPremium && (
              <div className={cnTokens(
                "absolute top-0 right-0 px-3 py-1 rounded-bl-lg",
                "bg-blue-500/10 border-b border-l border-blue-500/30"
              )}>
                <span className={cnTokens(typography.body.small, "text-blue-400 font-semibold")}>Current Plan</span>
              </div>
            )}
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={20} className="text-blue-400" />
                <h2 className={cnTokens(typography.sectionTitle, colors.text.primary)}>Premium</h2>
              </div>
              <div className="flex items-baseline gap-2 mb-4">
                <span className={cnTokens(typography.pageTitle, colors.text.primary)}>$7</span>
                <span className={cnTokens(typography.body.small, colors.text.secondary)}>/month</span>
              </div>
              <p className={cnTokens(typography.body.small, colors.text.secondary)}>
                Billed Monthly
              </p>
            </div>

            <div className={cnTokens(spacing.stack.md, "flex-1 mb-6")}>
              {features.premium.map((feature, index) => (
                <div key={index} className="flex items-start gap-3">
                  {feature.included ? (
                    <Check size={18} className={cnTokens(colors.text.success, "mt-0.5 flex-shrink-0")} />
                  ) : (
                    <X size={18} className={cnTokens(colors.text.muted, "mt-0.5 flex-shrink-0")} />
                  )}
                  <span className={cnTokens(
                    typography.body.default,
                    feature.included ? colors.text.primary : colors.text.muted
                  )}>
                    {feature.text}
                  </span>
                </div>
              ))}
            </div>

            <button
              onClick={() => {
                if (!isPremium) {
                  // Navigate to upgrade flow
                  // This would typically open a payment modal or redirect to Stripe
                  alert('Upgrade flow coming soon!')
                }
              }}
              disabled={isPremium}
              className={cnTokens(
                components.button.base,
                isPremium ? components.button.secondary : components.button.primary,
                "w-full",
                isPremium && "opacity-60 cursor-not-allowed"
              )}
            >
              {isPremium ? 'Your current plan' : 'Upgrade to Premium'}
            </button>
          </div>
        </div>

        {/* FAQ or Additional Info */}
        <div className={cnTokens(components.card.base, "max-w-3xl mx-auto")}>
          <h3 className={cnTokens(typography.subsectionTitle, colors.text.primary, "mb-4")}>
            Frequently Asked Questions
          </h3>
          <div className={cnTokens(spacing.stack.md)}>
            <div>
              <h4 className={cnTokens(typography.body.default, colors.text.primary, "mb-2")}>
                Can I switch plans anytime?
              </h4>
              <p className={cnTokens(typography.body.small, colors.text.secondary)}>
                Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately.
              </p>
            </div>
            <div>
              <h4 className={cnTokens(typography.body.default, colors.text.primary, "mb-2")}>
                What payment methods do you accept?
              </h4>
              <p className={cnTokens(typography.body.small, colors.text.secondary)}>
                We accept all major credit cards and debit cards through Stripe.
              </p>
            </div>
            <div>
              <h4 className={cnTokens(typography.body.default, colors.text.primary, "mb-2")}>
                Is there a free trial?
              </h4>
              <p className={cnTokens(typography.body.small, colors.text.secondary)}>
                Premium features are available immediately with a 14-day free trial. Cancel anytime during the trial.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

