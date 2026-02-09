import React, { useState, useRef, useEffect } from 'react'

interface VoiceRecorderProps {
  onRecordingComplete: (blob: Blob) => void
  maxDuration: number
  compact?: boolean  // NEW: Enable compact mode
}


export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onRecordingComplete,
  maxDuration,
  compact = true  // Default to compact mode
}) => {
  const [isRecording, setIsRecording] = useState(false)
  const [duration, setDuration] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)

  const clearTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    // Always reset state to ensure UI doesn't get stuck
    setIsRecording(false)
    clearTimer()
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder
      chunksRef.current = []
      setAudioUrl(null)
      setDuration(0)

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const url = URL.createObjectURL(blob)
        setAudioUrl(url)
        onRecordingComplete(blob)
        stream.getTracks().forEach((track) => track.stop())
        clearTimer()
      }

      recorder.start()
      setIsRecording(true)

      timerRef.current = window.setInterval(() => {
        setDuration((prev) => {
          if (prev + 1 >= maxDuration) {
            stopRecording()
          }
          return prev + 1
        })
      }, 1000)
    } catch (error) {
      console.error('Microphone access failed', error)
      alert('I could not access your microphone. Please check permissions.')
    }
  }

  useEffect(() => {
    return () => {
      clearTimer()
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
    }
  }, [audioUrl])

  // COMPACT MODE: Show only button when idle
  if (compact && !isRecording && !audioUrl) {
    return (
      <div className="voice-recorder voice-recorder--compact">
        <button
          type="button"
          className="button"
          onClick={startRecording}
          title="Record voice note"
        >
          🎤 Record voice note
        </button>
      </div>
    )
  }

  // EXPANDED MODE: Full interface
  return (
    <div className={`voice-recorder ${isRecording ? 'voice-recorder--expanded' : ''}`}>
      {!audioUrl ? (
        <>
          <div>
            <div className="voice-recorder__status">
              {isRecording ? 'Recording in progress…' : 'Ready to capture a note'}
            </div>
            <div className="voice-recorder__timer">
              {duration}s / {maxDuration}s
            </div>
          </div>
          {isRecording && (
            <div className="voice-wave" aria-hidden="true">
              <span className="voice-wave__bar" />
              <span className="voice-wave__bar" />
              <span className="voice-wave__bar" />
              <span className="voice-wave__bar" />
            </div>
          )}
          <button
            type="button"
            className={['button', isRecording ? 'button--danger' : ''].join(' ')}
            onClick={isRecording ? stopRecording : startRecording}
          >
            {isRecording ? 'Stop recording' : 'Start recording'}
          </button>
        </>
      ) : (
        <>
          <div>
            <div className="voice-recorder__status">Recording saved</div>
            <div className="voice-recorder__timer">
              Length {duration}s — review it below
            </div>
          </div>
          <audio
            src={audioUrl}
            controls
            style={{ width: '100%', maxWidth: '320px' }}
            aria-label="Recorded audio preview"
          />
          <button
            type="button"
            className="button button--quiet"
            onClick={() => {
              setAudioUrl(null)
              setDuration(0)
            }}
          >
            Record again
          </button>
        </>
      )}
    </div>
  )
}
