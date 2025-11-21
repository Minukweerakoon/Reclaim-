import React, { useState } from 'react'

interface ValidationCardProps {
  title: string
  data: unknown
}


export const ValidationCard: React.FC<ValidationCardProps> = ({ title, data }) => {
  const [open, setOpen] = useState(false)

  return (
    <div
      style={{
        border: '1px solid rgba(148, 163, 184, 0.3)',
        borderRadius: 12,
        padding: 12,
        background: 'rgba(11, 20, 38, 0.85)'
      }}
    >
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          width: '100%',
          cursor: 'pointer',
          background: 'transparent',
          border: 'none',
          color: '#e2e8f0',
          fontWeight: 600,
          fontSize: 14
        }}
        aria-expanded={open}
      >
        <span>{title}</span>
        <span>{open ? '-' : '+'}</span>
      </button>
      {open && (
        <pre
          style={{
            whiteSpace: 'pre-wrap',
            overflowX: 'auto',
            fontSize: 12,
            marginTop: 10,
            background: 'rgba(2, 6, 23, 0.55)',
            borderRadius: 8,
            padding: 10,
            border: '1px solid rgba(148, 163, 184, 0.2)'
          }}
        >
{JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  )
}
