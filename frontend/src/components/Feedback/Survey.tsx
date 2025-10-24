import React, { useState } from 'react'
import { Analytics } from '../../services/analytics'

export const Survey: React.FC<{ onSubmit?: () => void }>
  = ({ onSubmit }) => {
  const [score, setScore] = useState<number | null>(null)
  const [text, setText] = useState('')
  const submit = () => {
    Analytics.track('survey', { score, text })
    onSubmit?.()
  }
  return (
    <div style={{ border: '1px solid #1f2937', borderRadius: 12, padding: 12, background: '#0b1220' }}>
      <div style={{ marginBottom: 8 }}>How satisfied are you with this report experience?</div>
      <div>
        {[1,2,3,4,5].map(n => (
          <button key={n} onClick={() => setScore(n)} aria-pressed={score===n} style={{ marginRight: 6 }}>{n}</button>
        ))}
      </div>
      <textarea aria-label="Additional feedback" placeholder="Any feedback?" value={text} onChange={e => setText(e.target.value)} style={{ width: '100%', marginTop: 8, minHeight: 60, background: '#0b1220', color: '#e2e8f0', border: '1px solid #334155', borderRadius: 8 }} />
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
        <button onClick={submit} disabled={!score}>Submit</button>
      </div>
    </div>
  )
}

