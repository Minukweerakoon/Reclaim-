import { create } from 'zustand'

type Message = {
  id: string
  role: 'user' | 'bot'
  text?: string
  media?: { type: 'image' | 'audio', url: string }
  timestamp: number
}

type ApiConfig = { baseUrl: string; apiKey: string }

type State = {
  messages: Message[]
  api?: ApiConfig
  clientId: string
  sessionId: string
  confidence?: number
  analyticsOptIn: boolean
  demoMode: boolean
  presentationMode: boolean
}

type Actions = {
  addMessage: (m: Omit<Message, 'id' | 'timestamp'>) => void
  setApiConfig: (c: ApiConfig) => void
  setConfidence: (v: number) => void
  setAnalyticsOptIn: (v: boolean) => void
  toggleDemo: () => void
  togglePresentation: () => void
}

export const useAppStore = create<State & Actions>((set, get) => ({
  messages: [],
  clientId: Math.random().toString(36).slice(2),
  sessionId: Math.random().toString(36).slice(2),
  analyticsOptIn: true,
  demoMode: false,
  presentationMode: false,
  addMessage: (m) => set(state => ({
    messages: [...state.messages, { ...m, id: crypto.randomUUID(), timestamp: Date.now() }]
  })),
  setApiConfig: (c) => set({ api: c }),
  setConfidence: (v) => set({ confidence: v }),
  setAnalyticsOptIn: (v) => set({ analyticsOptIn: v }),
  toggleDemo: () => set(s => ({ demoMode: !s.demoMode })),
  togglePresentation: () => set(s => ({ presentationMode: !s.presentationMode }))
}))
