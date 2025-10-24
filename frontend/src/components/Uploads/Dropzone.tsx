import React, { useCallback, useRef, useState } from 'react'

export const Dropzone: React.FC<{ onFile: (f: File) => void; accept?: string }>
  = ({ onFile, accept }) => {
  const [hover, setHover] = useState(false)
  const inputRef = useRef<HTMLInputElement | null>(null)
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setHover(false)
    const f = e.dataTransfer.files[0]
    if (f) onFile(f)
  }, [onFile])
  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setHover(true) }}
      onDragLeave={() => setHover(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      style={{
        border: '2px dashed #334155', borderRadius: 12, padding: 20,
        background: hover ? '#0b1220' : '#0a1220', cursor: 'pointer'
      }}
      aria-label="File upload dropzone"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') inputRef.current?.click() }}
    >
      <div>Drag & drop or click to upload</div>
      <input ref={inputRef} type="file" accept={accept} onChange={e => {
        const f = e.target.files?.[0]
        if (f) onFile(f)
      }} style={{ display: 'none' }} />
    </div>
  )
}

