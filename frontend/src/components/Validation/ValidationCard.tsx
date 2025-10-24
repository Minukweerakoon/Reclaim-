import React, { useState } from 'react'

export const ValidationCard: React.FC<{ title: string; data: any }>
  = ({ title, data }) => {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ border: '1px solid #1f2937', borderRadius: 12, padding: 12, background: '#0b1220' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }} onClick={() => setOpen(!open)} aria-expanded={open} role="button" tabIndex={0}>
        <div>{title}</div>
        <div>{open ? '−' : '+'}</div>
      </div>
      {open && (
        <pre style={{ whiteSpace: 'pre-wrap', overflowX: 'auto', fontSize: 12, marginTop: 8 }} aria-label={`${title} details`}>
{JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  )
}

