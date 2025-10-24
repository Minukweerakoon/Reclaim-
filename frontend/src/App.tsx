import React, { useEffect } from 'react'
import { ChatWindow } from './components/Chat/ChatWindow'
import { useAppStore } from './state/store'

const App: React.FC = () => {
  const setApiConfig = useAppStore(s => s.setApiConfig)
  useEffect(() => {
    setApiConfig({
      baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      apiKey: import.meta.env.VITE_API_KEY || 'test-api-key'
    })
  }, [setApiConfig])
  return (
    <div style={{ minHeight: '100vh', display: 'flex', background: '#0f172a', color: '#e2e8f0' }}>
      <ChatWindow />
    </div>
  )
}

export default App

