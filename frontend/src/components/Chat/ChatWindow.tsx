import React, { useCallback, useState } from 'react'
import { useAppStore } from '../../state/store'
import { MessageBubble } from './MessageBubble'
import { Dropzone } from '../Uploads/Dropzone'
import { AudioRecorder } from '../Uploads/AudioRecorder'
import { postText, postImage, postAudio } from '../../services/api'
import { ScoreCircle } from '../Validation/ScoreCircle'
import { ValidationCard } from '../Validation/ValidationCard'
import { Survey } from '../Feedback/Survey'
import { DemoControls } from '../Demo/Controls'
import { ScreenRecorder } from '../Demo/ScreenRecorder'
import { useWebSocket } from '../../hooks/useWebSocket'
import { Analytics, Funnel } from '../../services/analytics'

export const ChatWindow: React.FC = () => {
  const { messages, addMessage } = useAppStore()
  const [input, setInput] = useState('')
  const [confidence, setConfidence] = useState<number | null>(null)
  const [lastResult, setLastResult] = useState<any | null>(null)
  const wsRef = useWebSocket()

  const send = useCallback(async () => {
    if (!input.trim()) return
    addMessage({ role: 'user', text: input })
    setInput('')
    try {
      Funnel.text()
      const res = await postText(input, 'auto')
      addMessage({ role: 'bot', text: res.message || 'Processed your text.' })
      if (typeof res.confidence === 'number') setConfidence(res.confidence)
      setLastResult(res)
      if (res.valid && res.confidence >= 0.7) Funnel.submit()
    } catch (e:any) {
      addMessage({ role: 'bot', text: `Sorry, text validation failed. ${e.message}` })
    }
  }, [input, addMessage])

  const onImage = async (f: File) => {
    addMessage({ role: 'user', text: `Uploaded image: ${f.name}` })
    try {
      Funnel.image()
      const res = await postImage(f)
      addMessage({ role: 'bot', text: res.message || 'Image checked.' })
      if (res.modal_scores?.image?.blur_detection?.variance !== undefined) {
        addMessage({ role: 'bot', text: `Sharpness: ${res.modal_scores.image.blur_detection.variance.toFixed(1)}` })
      }
      if (typeof res.confidence === 'number') setConfidence(res.confidence)
      setLastResult(res)
    } catch (e:any) {
      addMessage({ role: 'bot', text: `Sorry, image validation failed. ${e.message}` })
    }
  }

  const onAudioStop = async (blob: Blob) => {
    addMessage({ role: 'user', text: `Recorded audio (${(blob.size/1024).toFixed(0)} KB)` })
    try {
      Funnel.audio()
      const file = new File([blob], 'recording.webm', { type: 'audio/webm' })
      const res = await postAudio(file)
      addMessage({ role: 'bot', text: res.message || 'Audio processed.' })
      if (res.modal_scores?.audio?.transcription?.text) {
        addMessage({ role: 'bot', text: `Heard: "${res.modal_scores.audio.transcription.text}"` })
      }
      if (typeof res.confidence === 'number') setConfidence(res.confidence)
      setLastResult(res)
      if (res.valid && res.confidence >= 0.7) Funnel.success(res.confidence)
    } catch (e:any) {
      addMessage({ role: 'bot', text: `Sorry, audio validation failed. ${e.message}` })
    }
  }

  return (
    <div style={{ margin: '0 auto', maxWidth: 920, width: '100%', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <h1 style={{ fontSize: 18, margin: 0 }}>Multimodal Validation Assistant</h1>
        {confidence !== null && <ScoreCircle score={confidence} />}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <DemoControls onScenario={(s) => {
            if (s === 'iphone_red_library') {
              setInput('I lost my red iPhone 13 in the library')
              // Simulate sending
            }
          }} />
          <ScreenRecorder />
        </div>
      </div>
      <div role="log" aria-live="polite" style={{ flex: 1, overflowY: 'auto', background: '#0b1220', borderRadius: 12, padding: 12, border: '1px solid #1f2937' }}>
        {messages.map(m => (
          <MessageBubble key={m.id} role={m.role} time={m.timestamp}>{m.text}</MessageBubble>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          aria-label="Type your message"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') send() }}
          placeholder="Describe your lost item..."
          style={{ flex: 1, padding: 10, borderRadius: 8, border: '1px solid #334155', background: '#0b1220', color: '#e2e8f0' }}
        />
        <button onClick={send} aria-label="Send">Send</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 12 }}>
        <Dropzone onFile={onImage} accept="image/*" />
        <AudioRecorder onStop={onAudioStop} />
      </div>
      {lastResult && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 12 }}>
          <ValidationCard title="Explainability" data={lastResult.explain || {}} />
          <ValidationCard title="Modal Scores" data={lastResult.modal_scores || {}} />
        </div>
      )}
      <Survey />
    </div>
  )
}
