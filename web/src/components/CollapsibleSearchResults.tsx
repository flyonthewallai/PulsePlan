import { useState } from 'react'
import { ChevronDown, ChevronRight, Search, ExternalLink } from 'lucide-react'

interface SearchResult {
  title: string
  url: string
  content: string
  score?: number
  favicon?: string
  published_date?: string
  source?: string
}

interface CollapsibleSearchResultsProps {
  searchData: {
    query: string
    answer?: string
    results: SearchResult[]
    total_results: number
  }
}

export function CollapsibleSearchResults({ searchData }: CollapsibleSearchResultsProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url)
      return urlObj.hostname.replace('www.', '')
    } catch {
      return url
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return null
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      })
    } catch {
      return null
    }
  }

  return (
    <div className="bg-neutral-800/80 border border-gray-700/50 rounded-xl mb-6">
      {/* Collapsible Header */}
      <div 
        className="group p-4 cursor-pointer hover:bg-neutral-800/60 transition-colors duration-200 rounded-xl"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 bg-white rounded-full flex items-center justify-center">
              <Search size={12} className="text-neutral-800" />
            </div>
            <span className="text-white font-medium text-base">
              Sources ({searchData.total_results})
            </span>
          </div>
          <div className="text-gray-400 transition-all duration-200 group-hover:text-white">
            {isExpanded ? (
              <ChevronDown size={20} />
            ) : (
              <ChevronRight size={20} />
            )}
          </div>
        </div>
      </div>

      {/* Collapsible Content */}
      {isExpanded && (
        <div className="px-4 pb-4">
          {/* Search Sources */}
          <div 
            className="space-y-3 max-h-96 overflow-y-auto"
            style={{
              scrollbarWidth: 'thin',
              scrollbarColor: 'rgba(75, 85, 99, 0.5) transparent'
            }}
          >
            {searchData.results.map((result, index) => (
              <div 
                key={index}
                className="p-3 bg-neutral-700/50 rounded-lg hover:bg-neutral-700/60 transition-colors duration-150"
              >
                <div className="flex items-start gap-3">
                  {/* Favicon or default icon */}
                  <div className="w-4 h-4 mt-1 flex-shrink-0">
                    {result.favicon ? (
                      <img 
                        src={result.favicon} 
                        alt="" 
                        className="w-4 h-4 rounded-sm"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                    ) : (
                      <div className="w-4 h-4 bg-gray-500 rounded-sm"></div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Title */}
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <a 
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-white font-medium text-sm leading-tight hover:text-blue-300 transition-colors cursor-pointer"
                      >
                        {result.title}
                      </a>
                      <a 
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-400 hover:text-blue-300 transition-colors"
                      >
                        <ExternalLink size={12} className="flex-shrink-0 mt-0.5" />
                      </a>
                    </div>

                    {/* URL */}
                    <div className="text-xs text-gray-400 mb-2">
                      {formatUrl(result.url)}
                      {formatDate(result.published_date) && (
                        <span className="ml-2">• {formatDate(result.published_date)}</span>
                      )}
                    </div>

                    {/* Content snippet */}
                    <div className="text-xs text-gray-300 leading-relaxed line-clamp-3">
                      {result.content}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
