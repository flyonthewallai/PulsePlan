import { useNavigate } from 'react-router-dom'
import { Sparkles, Check, X } from 'lucide-react'
import { cn } from '../../lib/utils'
import { typography, colors, spacing, components, cn as cnTokens } from '../../lib/design-tokens'
import { useProfile } from '@/hooks/profile'

export function PremiumSection() {
  const navigate = useNavigate()
  const { data: profile } = useProfile()
  const isPremium = profile?.subscription_status === 'premium'

  return (
    <div className="space-y-6">
      <div className={cnTokens(components.card.base, "border-2 border-blue-500/30")}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <Sparkles size={24} className="text-blue-400" />
            </div>
            <div>
              <h3 className={cnTokens(typography.body.large, "font-semibold", colors.text.primary)}>
                {isPremium ? 'PulsePlan Premium' : 'Upgrade'}
              </h3>
              {isPremium && (
                <p className={cnTokens(typography.body.small, colors.text.secondary, "mt-0.5")}>
                  Your plan auto-renews on Nov 19, 2025
                </p>
              )}
            </div>
          </div>
          <button 
            onClick={() => navigate('/pricing')}
            className={cnTokens(components.button.base, components.button.secondary)}
          >
            {isPremium ? 'Manage' : 'Upgrade plan'}
          </button>
        </div>
        <div className={cnTokens(components.divider.horizontal, "my-4")}></div>
        {isPremium ? (
          <>
            <p className={cnTokens(typography.body.default, colors.text.secondary)}>
              Thanks for subscribing to PulsePlan Premium! Your Premium plan includes:
            </p>
            <div className={cnTokens(spacing.stack.md, "mt-4")}>
              {[
                'Basic task + deadline management',
                'Unlimited schedules per week',
                'Google/Apple Calendar integration',
                'Unlimited agent access',
                'Unlimited canvas sync (all courses)',
                'Unlimited task storage',
                'AI task breakdown & automation',
                'Smart auto-scheduling & rescheduling',
                'Long term memory of you',
                'Auto-draft & summarize emails',
                'Daily AI morning briefings',
                'Custom AI preferences',
                'Priority support & early access',
              ].map((feature, index) => (
                <div key={index} className="flex items-start gap-3">
                  <Check size={18} className={cnTokens(colors.text.success, "mt-0.5 flex-shrink-0")} />
                  <p className={cnTokens(typography.body.default, colors.text.primary)}>{feature}</p>
                </div>
              ))}
            </div>
          </>
        ) : (
          <>
            <p className={cnTokens(typography.body.default, colors.text.secondary)}>
              Upgrade to PulsePlan Premium to unlock advanced features:
            </p>
            <div className={cnTokens(spacing.stack.md, "mt-4")}>
              {[
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
              ].map((feature, index) => (
                <div key={index} className="flex items-start gap-3">
                  {feature.included ? (
                    <Check size={18} className={cnTokens(colors.text.success, "mt-0.5 flex-shrink-0")} />
                  ) : (
                    <X size={18} className={cnTokens(colors.text.muted, "mt-0.5 flex-shrink-0")} />
                  )}
                  <p className={cnTokens(
                    typography.body.default,
                    feature.included ? colors.text.primary : colors.text.muted
                  )}>
                    {feature.text}
                  </p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

