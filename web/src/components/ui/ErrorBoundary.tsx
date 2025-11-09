import React from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error?: Error; retry?: () => void }>
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  retry = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback
      return <FallbackComponent error={this.state.error} retry={this.retry} />
    }

    return this.props.children
  }
}

interface ErrorFallbackProps {
  error?: Error
  retry?: () => void
}

function DefaultErrorFallback({ error, retry }: ErrorFallbackProps) {
  return (
    <div className="min-h-screen w-full flex items-center justify-center px-6">
      <div className="w-full max-w-xl bg-neutral-900/60 border border-white/10 rounded-2xl shadow-xl p-6 text-center backdrop-blur-sm">
        <div className="mx-auto mb-4 w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
          <AlertTriangle className="w-6 h-6 text-amber-400" />
        </div>

        <h2 className="text-lg font-semibold text-white mb-2">Something went wrong</h2>

        <p className="text-sm text-gray-400 mb-3 line-clamp-3">
          {error?.message || 'An unexpected error occurred. Please try again.'}
        </p>

        {retry && (
          <button
            onClick={retry}
            className="inline-flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-lg bg-white text-black hover:bg-gray-100 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Try again
          </button>
        )}
      </div>
    </div>
  )
}

export { DefaultErrorFallback }