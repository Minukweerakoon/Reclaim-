import { useEffect, useRef } from 'react'
import { getWsUrl } from '../services/api'
import { useAppStore } from '../state/store'

export function useWebSocket() {
  const clientId = useAppStore(s => s.clientId)
  const addMessage = useAppStore(s => s.addMessage)
  const setConfidence = useAppStore(s => s.setConfidence)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const url = getWsUrl(clientId)
    const ws = new WebSocket(url)
    wsRef.current = ws
    ws.onopen = () => {
      // can send initial messages if needed
    }
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        if (typeof data.confidence === 'number') {
          setConfidence(data.confidence)
        }
        if (data.message && data.progress !== undefined) {
          addMessage({ role: 'bot', text: `${data.message} (${data.progress}%)` })
        }
      } catch {}
    }
    ws.onerror = () => {}
    ws.onclose = () => {}
    return () => {
      ws.close()
    }
  }, [clientId])

  return wsRef
}
