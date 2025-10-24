import React from 'react'

export const MessageBubble: React.FC<{ role: 'user'|'bot'; children: React.ReactNode; time?: number }>
  = ({ role, children, time }) => {
  const align = role === 'user' ? 'flex-end' : 'flex-start'
  const bg = role === 'user' ? '#22d3ee' : '#1f2937'
  const color = role === 'user' ? '#0f172a' : '#e2e8f0'
  return (
    <div style={{ display: 'flex', justifyContent: align, marginBottom: 8 }}>
      <div style={{ background: bg, color, padding: '8px 12px', borderRadius: 12, maxWidth: 560 }}>
        <div>{children}</div>
        {time && <div style={{ fontSize: 10, opacity: 0.7, marginTop: 4 }}>{new Date(time).toLocaleTimeString()}</div>}
      </div>
    </div>
  )
}

