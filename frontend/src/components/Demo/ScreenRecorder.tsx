import React, { useEffect, useRef, useState } from 'react'

export const ScreenRecorder: React.FC = () => {
  const [recording, setRecording] = useState(false)
  const [url, setUrl] = useState<string | null>(null)
  const recRef = useRef<MediaRecorder | null>(null)
  const chunks = useRef<BlobPart[]>([])
  const start = async () => {
    const stream = await (navigator.mediaDevices as any).getDisplayMedia({ video: true, audio: true })
    const rec = new MediaRecorder(stream)
    recRef.current = rec
    chunks.current = []
    rec.ondataavailable = (e) => chunks.current.push(e.data)
    rec.onstop = () => {
      const blob = new Blob(chunks.current, { type: 'video/webm' })
      setUrl(URL.createObjectURL(blob))
    }
    rec.start()
    setRecording(true)
  }
  const stop = () => { recRef.current?.stop(); setRecording(false) }
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      {!recording && <button onClick={start}>Start Screen</button>}
      {recording && <button onClick={stop}>Stop</button>}
      {url && <a href={url} download={`demo-${Date.now()}.webm`}>Download Recording</a>}
    </div>
  )
}

