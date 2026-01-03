import React, { useState } from 'react'
import { useTTS } from '../../hooks/useTTS'

interface Message {
  id: string
  type: 'bot' | 'user'
  content: string
  timestamp: Date
  metadata?: Record<string, unknown>
}


export const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const isBot = message.type === 'bot'
  const imageUrl = message.metadata?.imageUrl as string | undefined
  const feedbackRecorded = message.metadata?.feedbackRecorded as boolean | undefined

  const { speak, stop, isSpeaking } = useTTS()
  const [isThisMessageSpeaking, setIsThisMessageSpeaking] = useState(false)

  const handleSpeak = () => {
    if (isThisMessageSpeaking) {
      stop()
      setIsThisMessageSpeaking(false)
    } else {
      setIsThisMessageSpeaking(true)
      speak(message.content).finally(() => {
        setIsThisMessageSpeaking(false)
      })
    }
  }

  return (
    <div
      className="message-row"
      style={{
        display: 'flex',
        justifyContent: isBot ? 'flex-start' : 'flex-end'
      }}
    >
      <div
        className={[
          'message-bubble',
          isBot ? 'message-bubble--bot' : 'message-bubble--user',
          isThisMessageSpeaking ? 'message-bubble--speaking' : ''
        ].join(' ')}
      >
        {/* Display image if present */}
        {imageUrl && (
          <div className="message-image">
            <img
              src={imageUrl}
              alt="Uploaded"
              style={{
                maxWidth: '100%',
                maxHeight: '150px',
                borderRadius: '8px',
                marginBottom: '0.5rem',
                objectFit: 'cover'
              }}
            />
          </div>
        )}

        {/* Message content with speaker button for bot messages */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
          <p className="message-text" style={{ flex: 1, margin: 0 }}>{message.content}</p>

          {/* Speaker button for bot messages */}
          {isBot && (
            <button
              onClick={handleSpeak}
              className="tts-speaker-button"
              title={isThisMessageSpeaking ? 'Stop speaking' : 'Listen to message'}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1.2rem',
                padding: '0.25rem',
                opacity: isThisMessageSpeaking ? 1 : 0.6,
                transition: 'opacity 0.2s',
                flexShrink: 0
              }}
            >
              {isThisMessageSpeaking ? '🔊' : '🔈'}
            </button>
          )}
        </div>

        {/* Show feedback recorded indicator */}
        {feedbackRecorded && (
          <div
            className="feedback-badge"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              marginTop: '0.5rem',
              padding: '0.25rem 0.5rem',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '4px',
              fontSize: '0.7rem',
              color: '#10b981'
            }}
            title="Your correction helps improve the AI system"
          >
            <span>✓</span>
            <span>Feedback recorded</span>
          </div>
        )}

        <time
          className="message-timestamp"
          dateTime={message.timestamp.toISOString()}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </time>
      </div>
    </div>
  )
}
