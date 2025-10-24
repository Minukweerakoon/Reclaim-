import React from 'react'
import { useRecorder } from '../../hooks/useRecorder'

export const AudioRecorder: React.FC<{ onStop: (blob: Blob) => void }>
  = ({ onStop }) => {
  const { recording, blob, start, stop, canvasRef } = useRecorder()
  React.useEffect(() => { if (blob) onStop(blob) }, [blob, onStop])
  return (
    <div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        {!recording && <button onClick={start} aria-label="Start recording">Start</button>}
        {recording && <button onClick={stop} aria-label="Stop recording">Stop</button>}
        <canvas ref={canvasRef} width={300} height={60} aria-label="Audio waveform" />
      </div>
    </div>
  )
}

