import { useAppStore } from '../state/store'

type Event = { name: string; ts: number; data?: Record<string, any> }

export const Analytics = {
  track(name: string, data?: Record<string, any>) {
    const { analyticsOptIn, sessionId } = useAppStore.getState()
    if (!analyticsOptIn) return
    const evt: Event = { name, ts: Date.now(), data: { ...data, sessionId } }
    const buf = JSON.parse(localStorage.getItem('events') || '[]') as Event[]
    buf.push(evt)
    localStorage.setItem('events', JSON.stringify(buf))
    // Placeholder: send to server if endpoint exists
    // fetch('/analytics', { method: 'POST', body: JSON.stringify(evt) })
    console.debug('[analytics]', evt)
  },
  clear() { localStorage.removeItem('events') },
  export() { return localStorage.getItem('events') || '[]' }
}

export const Funnel = {
  start() { Analytics.track('funnel_start') },
  text() { Analytics.track('funnel_text') },
  image() { Analytics.track('funnel_image') },
  audio() { Analytics.track('funnel_audio') },
  submit() { Analytics.track('funnel_submit') },
  success(conf?: number) { Analytics.track('funnel_success', { confidence: conf }) }
}

