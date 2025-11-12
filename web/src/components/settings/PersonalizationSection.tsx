import { useState } from 'react'
import { cn } from '../../lib/utils'
import { components } from '../../lib/design-tokens'
import { useUpdateProfile } from '@/hooks/profile'

interface PersonalizationSectionProps {
  agentInstructions: string
  setAgentInstructions: (value: string) => void
  agentMemories: string
  setAgentMemories: (value: string) => void
  onSaveProfile: () => void
}

export function PersonalizationSection({
  agentInstructions,
  setAgentInstructions,
  agentMemories,
  setAgentMemories,
  onSaveProfile,
}: PersonalizationSectionProps) {
  const updateProfileMutation = useUpdateProfile()
  const [personalizationSavedAt, setPersonalizationSavedAt] = useState<string | null>(null)

  const savePersonalization = async () => {
    try {
      await updateProfileMutation.mutateAsync({
        agent_instructions: agentInstructions,
        agent_memories: agentMemories,
      } as any)
      setPersonalizationSavedAt(new Date().toISOString())
    } catch (e) {
      console.error('Failed saving personalization', e)
      alert('Failed to save. Please try again.')
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Agent Instructions</h3>
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
          <div className="p-4">
            <textarea
              value={agentInstructions}
              onChange={(e) => setAgentInstructions(e.target.value)}
              placeholder="Tell Pulse how you'd like it to behave. Ex: Be concise, prefer bullet points, always confirm before deleting."
              className="w-full bg-transparent text-white placeholder-gray-500 text-sm outline-none resize-y min-h-[100px]"
            />
            <div className="mt-2 text-xs text-gray-500">Saved to your profile. Applied across devices.</div>
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Memories</h3>
          <span className="text-xs text-gray-500">{agentMemories.length}/500</span>
        </div>
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
          <div className="p-4">
            <textarea
              value={agentMemories}
              onChange={(e) => setAgentMemories(e.target.value.slice(0,500))}
              placeholder="Ex: I'm a CS student, part‑time barista, evenings are best for studying, prefer weekly planning on Sundays."
              className="w-full bg-transparent text-white placeholder-gray-500 text-sm outline-none resize-y min-h-[140px]"
              maxLength={500}
            />
            <p className="mt-2 text-xs text-gray-500">Context Pulse can reference when helping you (preferences, routines, constraints).</p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onSaveProfile}
          className={cn(components.button.base, components.button.primary)}
        >
          Save
        </button>
        <button
          onClick={savePersonalization}
          className={cn(components.button.base, components.button.secondary)}
        >
          Save Agent Personalization
        </button>
        {personalizationSavedAt && (
          <span className="text-xs text-gray-500">Saved {new Date(personalizationSavedAt).toLocaleTimeString()}</span>
        )}
      </div>
    </div>
  )
}

