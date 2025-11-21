import React from 'react'

interface Message {
  id: string
  type: 'bot' | 'user'
  content: string
  timestamp: Date
  metadata?: Record<string, unknown>
}


export const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const isBot = message.type === 'bot'

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
          isBot ? 'message-bubble--bot' : 'message-bubble--user'
        ].join(' ')}
      >
        <p className="message-text">{message.content}</p>
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
