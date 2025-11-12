import { cn } from '../../lib/utils'
import { components } from '../../lib/design-tokens'

export function AppearanceSection() {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Choose a Theme</h3>
        <div className="space-y-2">
          {[
            { id: 'dark', name: 'Dark', preview: 'bg-gray-800', selected: true },
            { id: 'light', name: 'Light', preview: 'bg-white', selected: false },
          ].map((theme) => (
            <div
              key={theme.id}
              className="flex items-center gap-3 p-3 rounded-lg transition-colors cursor-pointer bg-neutral-800/40 border border-gray-700/50 hover:bg-neutral-800/60"
            >
              <div className={cn("w-10 h-10 rounded-md", theme.preview)} />
              <div className="flex-1 flex items-center gap-2">
                <span className="text-white text-sm font-medium">{theme.name}</span>
              </div>
              <div className="w-5 h-5 rounded-full border-2 border-gray-500 flex items-center justify-center">
                {theme.selected && <div className="w-2.5 h-2.5 bg-blue-500 rounded-full" />}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

