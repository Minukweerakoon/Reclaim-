import { useEffect, useRef, useState } from 'react'

export function useRecorder() {
  const [recording, setRecording] = useState(false)
  const [blob, setBlob] = useState<Blob | null>(null)
  const mediaRef = useRef<MediaRecorder | null>(null)
  const audioChunks = useRef<BlobPart[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const rafRef = useRef<number | null>(null)

  useEffect(() => () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }, [])

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const ctx = new AudioContext()
    const source = ctx.createMediaStreamSource(stream)
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 2048
    source.connect(analyser)
    analyserRef.current = analyser
    const rec = new MediaRecorder(stream)
    mediaRef.current = rec
    audioChunks.current = []
    rec.ondataavailable = (e) => { audioChunks.current.push(e.data) }
    rec.onstop = () => {
      const b = new Blob(audioChunks.current, { type: 'audio/webm' })
      setBlob(b)
    }
    rec.start()
    setRecording(true)
    draw()
  }

  const stop = () => {
    mediaRef.current?.stop()
    setRecording(false)
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
  }

  const draw = () => {
    const analyser = analyserRef.current
    const canvas = canvasRef.current
    if (!analyser || !canvas) return
    const ctx = canvas.getContext('2d')!
    const bufferLength = analyser.fftSize
    const dataArray = new Uint8Array(bufferLength)
    const render = () => {
      analyser.getByteTimeDomainData(dataArray)
      ctx.fillStyle = '#0f172a'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.lineWidth = 2
      ctx.strokeStyle = '#22d3ee'
      ctx.beginPath()
      const sliceWidth = canvas.width / bufferLength
      let x = 0
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0
        const y = (v * canvas.height) / 2
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
        x += sliceWidth
      }
      ctx.lineTo(canvas.width, canvas.height / 2)
      ctx.stroke()
      rafRef.current = requestAnimationFrame(render)
    }
    rafRef.current = requestAnimationFrame(render)
  }

  return { recording, blob, start, stop, audioRef, canvasRef }
}

