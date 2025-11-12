import { useState, useEffect } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { cn } from '../../lib/utils'
import { components } from '../../lib/design-tokens'
import { tagsApi, type Tag } from '../../services/user'
import { tagCreationSchema, validateInput } from '../../lib/validation/settings'

export function TagsSection() {
  const [tags, setTags] = useState<Tag[]>([])
  const [tagsLoading, setTagsLoading] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const [isCreatingTag, setIsCreatingTag] = useState(false)

  const fetchTags = async (signal?: AbortSignal) => {
    try {
      setTagsLoading(true)
      const data = await tagsApi.getAllTags()
      if (!signal?.aborted) {
        setTags(data)
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }
      if (!signal?.aborted) {
        console.error('Failed to fetch tags:', error)
      }
    } finally {
      if (!signal?.aborted) {
        setTagsLoading(false)
      }
    }
  }

  useEffect(() => {
    const abortController = new AbortController()
    fetchTags(abortController.signal)
    
    return () => {
      abortController.abort()
    }
  }, [])

  const handleCreateTag = async () => {
    const validation = validateInput(tagCreationSchema, {
      name: newTagName,
    })
    
    if (!validation.success) {
      alert(validation.error)
      return
    }

    try {
      setIsCreatingTag(true)
      await tagsApi.createUserTag(validation.data.name)
      setNewTagName('')
      await fetchTags()
    } catch (error: unknown) {
      console.error('Failed to create tag:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create tag'
      alert(errorMessage)
    } finally {
      setIsCreatingTag(false)
    }
  }

  const handleDeleteTag = async (tag: Tag) => {
    if (tag.type !== 'user') return
    
    if (!confirm(`Are you sure you want to delete the "${tag.name}" tag?`)) {
      return
    }

    try {
      if (tag.id) {
        await tagsApi.deleteUserTag(tag.id)
      } else {
        await tagsApi.deleteUserTagByName(tag.name)
      }
      await fetchTags()
    } catch (error) {
      console.error('Failed to delete tag:', error)
      alert('Failed to delete tag')
    }
  }

  const predefinedTags = tags.filter(t => t.type === 'predefined')
  const userTags = tags.filter(t => t.type === 'user')

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-400 mb-3">
        Pulse automatically applies predefined tags to your tasks. Add your own custom tags to organize tasks however you want.
      </p>

      <div className="mb-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            placeholder="Create new tag..."
            onKeyPress={(e) => e.key === 'Enter' && handleCreateTag()}
            className={cn(components.input.base, "flex-1")}
          />
          <button
            onClick={handleCreateTag}
            disabled={!newTagName.trim() || isCreatingTag}
            className={cn(
              components.button.base,
              components.button.primary,
              "flex items-center gap-1 disabled:bg-gray-200 disabled:cursor-not-allowed"
            )}
          >
            <Plus size={12} />
            Add
          </button>
        </div>
      </div>

      {userTags.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Your Tags</h4>
          <div className="flex flex-wrap gap-2">
            {userTags.map((tag) => (
              <div
                key={`${tag.name}-${tag.id || 'no-id'}`}
                className="bg-neutral-800/40 rounded-lg px-2 py-1 flex items-center gap-1.5"
              >
                <span className="text-xs text-white">{tag.name}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDeleteTag(tag)
                  }}
                  className="text-gray-500 hover:text-red-400 transition-colors"
                  title="Delete tag"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Predefined Tags</h4>
        {predefinedTags.length === 0 ? (
          <p className="text-gray-500 text-sm">No predefined tags available.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {predefinedTags.map((tag) => (
              <div
                key={tag.name}
                className="bg-neutral-800/40 rounded-lg px-2 py-1 flex items-center gap-1.5"
              >
                <span className="text-xs text-white">{tag.name}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {tagsLoading && (
        <div className="flex items-center justify-center py-12">
          <p className="text-gray-400">Loading tags...</p>
        </div>
      )}
    </div>
  )
}

