interface ToastState {
  toasts: Array<{
    id: string
    title: string
    description?: string
    type: 'success' | 'error' | 'warning' | 'info' | 'loading'
    duration?: number
  }>
}

let listeners: Array<(state: ToastState) => void> = []
let state: ToastState = { toasts: [] }

const updateState = (newState: ToastState) => {
  state = newState
  listeners.forEach(listener => listener(state))
}

export const toast = {
  loading: (title: string, description?: string, duration = 8000) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast = { id, title, description, type: 'loading' as const, duration }
    
    updateState({
      toasts: [...state.toasts, newToast]
    })
    
    setTimeout(() => {
      updateState({
        toasts: state.toasts.filter(t => t.id !== id)
      })
    }, duration)
    
    return id
  },
  success: (title: string, description?: string, duration = 5000) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast = { id, title, description, type: 'success' as const, duration }
    
    updateState({
      toasts: [...state.toasts, newToast]
    })
    
    setTimeout(() => {
      updateState({
        toasts: state.toasts.filter(t => t.id !== id)
      })
    }, duration)
    
    return id
  },
  
  error: (title: string, description?: string, duration = 7000) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast = { id, title, description, type: 'error' as const, duration }
    
    updateState({
      toasts: [...state.toasts, newToast]
    })
    
    setTimeout(() => {
      updateState({
        toasts: state.toasts.filter(t => t.id !== id)
      })
    }, duration)
    
    return id
  },
  
  warning: (title: string, description?: string, duration = 6000) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast = { id, title, description, type: 'warning' as const, duration }
    
    updateState({
      toasts: [...state.toasts, newToast]
    })
    
    setTimeout(() => {
      updateState({
        toasts: state.toasts.filter(t => t.id !== id)
      })
    }, duration)
    
    return id
  },
  
  info: (title: string, description?: string, duration = 5000) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast = { id, title, description, type: 'info' as const, duration }
    
    updateState({
      toasts: [...state.toasts, newToast]
    })
    
    setTimeout(() => {
      updateState({
        toasts: state.toasts.filter(t => t.id !== id)
      })
    }, duration)
    
    return id
  },
  
  dismiss: (id: string) => {
    updateState({
      toasts: state.toasts.filter(t => t.id !== id)
    })
  },
  
  dismissAll: () => {
    updateState({ toasts: [] })
  },
  
  subscribe: (listener: (state: ToastState) => void) => {
    listeners.push(listener)
    listener(state)
    
    return () => {
      listeners = listeners.filter(l => l !== listener)
    }
  }
}