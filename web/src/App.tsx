import React from 'react'
import { Providers } from './app/providers'
import { AppRoutes } from './app/routes'
import { ToastContainer } from './components/ui/Toast'
import './index.css'

function App() {
  return (
    <Providers>
      <AppRoutes />
      <ToastContainer />
    </Providers>
  )
}

export default App