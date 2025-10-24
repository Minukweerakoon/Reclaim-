import React from 'react'

export const ScoreCircle: React.FC<{ score: number; size?: number }>
  = ({ score, size = 56 }) => {
  const radius = (size / 2) - 4
  const circ = 2 * Math.PI * radius
  const pct = Math.max(0, Math.min(1, score))
  const offset = circ - pct * circ
  const color = pct >= 0.85 ? '#22c55e' : pct >= 0.7 ? '#eab308' : '#ef4444'
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size/2} cy={size/2} r={radius} stroke="#334155" strokeWidth={4} fill="none" />
      <circle cx={size/2} cy={size/2} r={radius} stroke={color} strokeWidth={4} fill="none"
        strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" transform={`rotate(-90 ${size/2} ${size/2})`} />
      <text x="50%" y="52%" dominantBaseline="middle" textAnchor="middle" fontSize={12} fill="#e2e8f0">
        {(pct*100).toFixed(0)}%
      </text>
    </svg>
  )
}

