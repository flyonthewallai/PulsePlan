import { useState } from 'react'
import { Plus, Pen, Trash2, X, Music, Camera, Book, Gamepad2, Palette, Dumbbell, Bike, Coffee, Film, Heart, Users, Target, Mountain, MountainSnow } from 'lucide-react'
import { cn } from '../../lib/utils'
import { components, spacing } from '../../lib/design-tokens'
import { useHobbies, useCreateHobby, useUpdateHobby, useDeleteHobby } from '@/hooks/integrations'
import { hobbiesApi, type Hobby as HobbyAPI } from '../../lib/api/sdk'
import { AddHobbyPrompt } from '../hobbies'
import { HobbySummary } from '../hobbies'

type Hobby = HobbyAPI & {
  // Add local-only fields if needed
}

const getHobbyIcon = (icon: string, className?: string) => {
  const props = { size: 16, className: cn('text-gray-400', className) }
  switch (icon) {
    case 'Music': return <Music {...props} />
    case 'Camera': return <Camera {...props} />
    case 'Book': return <Book {...props} />
    case 'Gamepad2': return <Gamepad2 {...props} />
    case 'Palette': return <Palette {...props} />
    case 'Dumbbell': return <Dumbbell {...props} />
    case 'Bike': return <Bike {...props} />
    case 'Coffee': return <Coffee {...props} />
    case 'Film': return <Film {...props} />
    case 'Heart': return <Heart {...props} />
    case 'Users': return <Users {...props} />
    case 'Snowflake': return <Target {...props} />
    case 'MountainSnow': return <MountainSnow {...props} />
    case 'Mountain': return <Mountain {...props} />
    default: return <Target {...props} />
  }
}

export function HobbiesSection() {
  const { data: hobbies = [] } = useHobbies()
  const createHobbyMutation = useCreateHobby()
  const updateHobbyMutation = useUpdateHobby()
  const deleteHobbyMutation = useDeleteHobby()

  const [selectedHobby, setSelectedHobby] = useState<Partial<Hobby> | null>(null)
  const [showHobbyModal, setShowHobbyModal] = useState(false)
  const [showAddHobbyPrompt, setShowAddHobbyPrompt] = useState(false)
  const [showHobbySummary, setShowHobbySummary] = useState(false)
  const [parsedHobby, setParsedHobby] = useState<any>(null)
  const [hobbyConfidence, setHobbyConfidence] = useState(1.0)
  const [isParsingHobby, setIsParsingHobby] = useState(false)

  const handleAddHobby = () => {
    setShowAddHobbyPrompt(true)
  }

  const handleHobbyDescriptionSubmit = async (description: string) => {
    setIsParsingHobby(true)
    try {
      const result = await hobbiesApi.parseHobby(description)
      if (result.success && result.hobby) {
        setParsedHobby(result.hobby)
        setHobbyConfidence(result.confidence)
        setShowAddHobbyPrompt(false)
        setShowHobbySummary(true)
      } else {
        alert(result.error || 'Failed to parse hobby description')
      }
    } catch (error) {
      console.error('Error parsing hobby:', error)
      alert('Failed to parse hobby description. Please try again.')
    } finally {
      setIsParsingHobby(false)
    }
  }

  const handleHobbyConfirm = async () => {
    if (!parsedHobby) return
    try {
      await createHobbyMutation.mutateAsync({
        name: parsedHobby.name,
        icon: parsedHobby.icon,
        preferred_time: parsedHobby.preferred_time,
        specific_time: parsedHobby.specific_time,
        days: parsedHobby.days,
        duration_min: parsedHobby.duration.min,
        duration_max: parsedHobby.duration.max,
        flexibility: parsedHobby.flexibility,
        notes: parsedHobby.notes,
      })
      setShowHobbySummary(false)
      setParsedHobby(null)
    } catch (error) {
      console.error('Error creating hobby:', error)
      alert('Failed to save hobby. Please try again.')
    }
  }

  const handleHobbyEdit = () => {
    if (!parsedHobby) return
    setSelectedHobby({
      name: parsedHobby.name,
      icon: parsedHobby.icon,
      preferred_time: parsedHobby.preferred_time,
      specific_time: parsedHobby.specific_time,
      days: parsedHobby.days,
      duration_min: parsedHobby.duration.min,
      duration_max: parsedHobby.duration.max,
      flexibility: parsedHobby.flexibility,
      notes: parsedHobby.notes,
    })
    setShowHobbySummary(false)
    setShowHobbyModal(true)
  }

  const handleEditHobby = (h: Hobby) => {
    setSelectedHobby(h)
    setShowHobbyModal(true)
  }

  const handleSaveHobby = async () => {
    if (!selectedHobby) return
    try {
      if (selectedHobby.id) {
        await updateHobbyMutation.mutateAsync({
          id: selectedHobby.id,
          updates: {
            name: selectedHobby.name!,
            icon: selectedHobby.icon!,
            preferred_time: selectedHobby.preferred_time!,
            specific_time: selectedHobby.specific_time,
            days: selectedHobby.days!,
            duration_min: selectedHobby.duration_min!,
            duration_max: selectedHobby.duration_max!,
            flexibility: selectedHobby.flexibility!,
            notes: selectedHobby.notes!,
          },
        })
      } else {
        await createHobbyMutation.mutateAsync({
          name: selectedHobby.name!,
          icon: selectedHobby.icon!,
          preferred_time: selectedHobby.preferred_time!,
          specific_time: selectedHobby.specific_time || null,
          days: selectedHobby.days!,
          duration_min: selectedHobby.duration_min!,
          duration_max: selectedHobby.duration_max!,
          flexibility: selectedHobby.flexibility!,
          notes: selectedHobby.notes || '',
        })
      }
      setShowHobbyModal(false)
      setSelectedHobby(null)
    } catch (error) {
      console.error('Error saving hobby:', error)
      alert('Failed to save hobby. Please try again.')
    }
  }

  const handleDeleteHobby = async (id: string) => {
    if (!confirm('Are you sure you want to delete this hobby?')) return
    try {
      await deleteHobbyMutation.mutateAsync({ id })
    } catch (error) {
      console.error('Error deleting hobby:', error)
      alert('Failed to delete hobby. Please try again.')
    }
  }

  return (
    <>
      <div className="space-y-4">
        <div>
          <p className="text-gray-400 text-sm">Add your hobbies and interests. PulsePlan will intelligently make time for them.</p>
        </div>
        <div className="flex items-center justify-end">
          <button
            onClick={handleAddHobby}
            className={cn(components.button.base, components.button.primary, "flex items-center gap-1")}
          >
            <Plus size={12} />
            Add Hobby
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {hobbies.map((hobby) => (
            <div key={hobby.id} className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4 flex items-start gap-3">
              <div className="shrink-0 mt-0.5">{getHobbyIcon(hobby.icon)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-white text-sm font-medium truncate">{hobby.name || 'Untitled'}</h4>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleEditHobby(hobby)}
                      className="p-1.5 text-gray-400 hover:text-white hover:bg-neutral-700/40 rounded transition-colors"
                      title="Edit hobby"
                    >
                      <Pen size={14} />
                    </button>
                    <button
                      onClick={() => handleDeleteHobby(hobby.id)}
                      className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                      title="Delete hobby"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-1 line-clamp-2">{hobby.notes}</p>
                <div className="mt-2 text-xs text-gray-500">
                  {hobby.preferred_time} • {hobby.duration_min === hobby.duration_max ? `${hobby.duration_min} min` : `${hobby.duration_min}-${hobby.duration_max} min`}
                </div>
              </div>
            </div>
          ))}
        </div>

        {showHobbyModal && selectedHobby && (
          <div className={components.modal.overlay}>
            <div className={cn(components.modal.container, "max-w-md")}>
              <div className={components.modal.header}>
                <div className="flex items-center justify-between w-full">
                  <h3 className={components.modal.title}>{selectedHobby.name ? 'Edit Hobby' : 'Add Hobby'}</h3>
                  <button onClick={() => { setShowHobbyModal(false); setSelectedHobby(null) }} className="text-gray-400 hover:text-white transition-colors">
                    <X size={18} />
                  </button>
                </div>
              </div>
              <div className={cn(components.modal.content, spacing.stack.md)}>
                <div>
                  <label className={components.input.label}>Name</label>
                  <input className={cn(components.input.base, "w-full")} value={selectedHobby.name} onChange={(e) => setSelectedHobby({ ...selectedHobby, name: e.target.value })} />
                </div>
                <div>
                  <label className={components.input.label}>Notes</label>
                  <textarea className={cn(components.textarea.base, "w-full min-h-[80px]")} value={selectedHobby.notes || ''} onChange={(e) => setSelectedHobby({ ...selectedHobby, notes: e.target.value })} />
                </div>
                <div>
                  <label className={components.input.label}>Preferred Time</label>
                  <select className={cn(components.select.base, "w-full")} value={selectedHobby.preferred_time} onChange={(e) => setSelectedHobby({ ...selectedHobby, preferred_time: e.target.value as any })}>
                    <option value="morning">Morning</option>
                    <option value="afternoon">Afternoon</option>
                    <option value="evening">Evening</option>
                    <option value="night">Night</option>
                    <option value="any">Anytime</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={components.input.label}>Min Duration (min)</label>
                    <input type="number" min={5} step={5} className={cn(components.input.base, "w-full")} value={selectedHobby.duration_min || 30} onChange={(e) => setSelectedHobby({ ...selectedHobby, duration_min: Number(e.target.value) })} />
                  </div>
                  <div>
                    <label className={components.input.label}>Max Duration (min)</label>
                    <input type="number" min={5} step={5} className={cn(components.input.base, "w-full")} value={selectedHobby.duration_max || 60} onChange={(e) => setSelectedHobby({ ...selectedHobby, duration_max: Number(e.target.value) })} />
                  </div>
                </div>
                <div>
                  <label className={components.input.label}>Flexibility</label>
                  <select className={cn(components.select.base, "w-full")} value={selectedHobby.flexibility} onChange={(e) => setSelectedHobby({ ...selectedHobby, flexibility: e.target.value as any })}>
                    <option value="low">Low (strict timing)</option>
                    <option value="medium">Medium (somewhat flexible)</option>
                    <option value="high">High (very flexible)</option>
                  </select>
                </div>
                <div>
                  <label className={components.input.label}>Icon</label>
                  <div className="mt-1 grid grid-cols-7 gap-1.5">
                    {(['Music','Camera','Book','Gamepad2','Palette','Dumbbell','Bike','Coffee','Film','Heart','Users','Target','Mountain','MountainSnow'] as any[]).map((i) => (
                      <button key={i} onClick={() => setSelectedHobby({ ...selectedHobby, icon: i })} className={cn('p-1 rounded border transition-colors aspect-square flex items-center justify-center', selectedHobby.icon === i ? 'border-white/70 bg-white/10' : 'border-gray-700/50 hover:bg-neutral-800/40')}>{getHobbyIcon(i)}</button>
                    ))}
                  </div>
                </div>
              </div>
              <div className={components.modal.footer}>
                <button onClick={() => { setShowHobbyModal(false); setSelectedHobby(null) }} className={cn(components.button.base, components.button.secondary)}>Cancel</button>
                <button onClick={handleSaveHobby} className={cn(components.button.base, components.button.primary)}>Save</button>
              </div>
            </div>
          </div>
        )}
      </div>

      <AddHobbyPrompt
        isOpen={showAddHobbyPrompt}
        onClose={() => setShowAddHobbyPrompt(false)}
        onSubmit={handleHobbyDescriptionSubmit}
        isLoading={isParsingHobby}
      />

      <HobbySummary
        isOpen={showHobbySummary}
        hobby={parsedHobby}
        confidence={hobbyConfidence}
        onClose={() => {
          setShowHobbySummary(false)
          setParsedHobby(null)
        }}
        onConfirm={handleHobbyConfirm}
        onEdit={handleHobbyEdit}
      />
    </>
  )
}

