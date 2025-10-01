import { useState } from 'react'
import { X, CheckCircle, Info, Play } from 'lucide-react'
import { canvasService } from '../services/canvasService'

type Props = {
  isOpen: boolean
  onClose: () => void
  onConnected: () => void
}

export function CanvasAPIConnectionModal({ isOpen, onClose, onConnected }: Props) {
  const [canvasDomain, setCanvasDomain] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showVideoModal, setShowVideoModal] = useState(false)

  const handleBackdrop = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isConnecting) onClose()
  }

  const handleConnect = async () => {
    setError(null)
    if (!canvasDomain.trim() || !apiKey.trim()) {
      setError('Please enter both Canvas domain and API key')
      return
    }
    const domainRegex = /^https?:\/\/[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    if (!domainRegex.test(canvasDomain.trim())) {
      setError('Enter a valid Canvas domain, e.g. https://your-school.instructure.com')
      return
    }
    try {
      setIsConnecting(true)
      await canvasService.connectWithAPIKey(canvasDomain.trim(), apiKey.trim())
      
      // Wait a moment for the backend to process the connection
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      onConnected()
      onClose()
    } catch (e: any) {
      setError(e?.message || 'Failed to connect Canvas')
    } finally {
      setIsConnecting(false)
    }
  }

  return (
    <div
      className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 transition-all duration-300 ${
        isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}
      onClick={handleBackdrop}
    >
      <div
        className={`bg-neutral-800 border border-gray-700/50 w-full max-w-xl rounded-2xl max-h-[85vh] flex flex-col transition-all duration-300 ${
          isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700/50">
          <div className="flex items-center gap-2">
            <img src="/canvas.png" alt="Canvas" className="w-5 h-5" />
            <h2 className="text-white font-semibold">Canvas</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-neutral-800 rounded-lg transition-colors"
            disabled={isConnecting}
            aria-label="Close"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto">
          {/* Instructions */}
          <div className="bg-neutral-800/60 border border-gray-700/50 rounded-xl p-4 mb-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-white font-medium">How to get your Canvas API key</h3>
              <button
                type="button"
                onClick={() => setShowVideoModal(true)}
                className="p-1 hover:text-white transition-colors group"
                title="Watch demo video"
              >
                <Info className="w-4 h-4 text-gray-400 group-hover:text-white" />
              </button>
            </div>
            <ol className="space-y-3 list-decimal list-inside text-sm text-gray-300">
              <li>Go to your Canvas domain (your school's Canvas website)</li>
              <li>Open Profile → Settings</li>
              <li>Under Approved Integrations, click New Access Token</li>
              <li>Enter purpose "PulsePlan", leave other fields blank, then copy the token</li>
            </ol>
          </div>

          {/* Inputs */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-300 mb-1">Canvas Domain</label>
              <input
                type="url"
                placeholder="https://your-school.instructure.com"
                value={canvasDomain}
                onChange={(e) => setCanvasDomain(e.target.value)}
                className="w-full bg-neutral-900 text-white border border-gray-700 rounded-lg px-3 py-2 placeholder:text-gray-500 focus:outline-none focus:border-gray-600"
                disabled={isConnecting}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">API Key</label>
              <input
                type="password"
                placeholder="Paste your Canvas API token"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full bg-neutral-900 text-white border border-gray-700 rounded-lg px-3 py-2 placeholder:text-gray-500 focus:outline-none focus:border-gray-600"
                disabled={isConnecting}
              />
            </div>
            {error && (
              <div className="text-red-400 text-sm">{error}</div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700/50 flex justify-end">
          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className={`px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-colors ${
              isConnecting ? 'bg-gray-300 text-black opacity-80' : 'bg-white text-black hover:bg-gray-100'
            }`}
          >
            <CheckCircle className="w-4 h-4" />
            {isConnecting ? 'Connecting...' : 'Connect'}
          </button>
        </div>
      </div>

      {/* Video Demo Modal */}
      {showVideoModal && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-[60] p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowVideoModal(false)
          }}
        >
          <div className="bg-neutral-800 border border-gray-700/50 w-full max-w-2xl rounded-2xl max-h-[85vh] flex flex-col">
            {/* Video Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700/50">
              <div className="flex items-center gap-2">
                <Play className="w-5 h-5 text-gray-400" />
                <h3 className="text-white font-semibold">Canvas API Key Demo</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowVideoModal(false)}
                className="p-1 hover:text-white transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Video Content */}
            <div className="p-4 flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-neutral-700 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Play className="w-8 h-8 text-gray-400" />
                </div>
                <h4 className="text-white font-medium mb-2">Demo Video Coming Soon</h4>
                <p className="text-gray-400 text-sm max-w-md">
                  We're working on a step-by-step video guide to help you find your Canvas API key. 
                  For now, please follow the written instructions above.
                </p>
                <button
                  onClick={() => setShowVideoModal(false)}
                  className="mt-4 px-4 py-2 bg-white text-black text-sm font-medium rounded-md hover:bg-gray-100 transition-colors"
                >
                  Got it
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


