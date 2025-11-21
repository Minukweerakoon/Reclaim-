import React, { useRef, useEffect } from 'react'
import { MessageBubble } from './MessageBubble'

interface Message {
  id: string
  type: 'bot' | 'user'
  content: string
  timestamp: Date
  metadata?: Record<string, unknown>
}


interface ChatInterfaceProps {
  messages: Message[]
  isProcessing: boolean
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, isProcessing }) => {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
  }, [messages, isProcessing])

  return (
    <div className="message-list" ref={containerRef}>
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {isProcessing && (
        <div className="typing-indicator" role="status" aria-live="polite">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span>Processing...</span>
        </div>
      )}
    </div>
  )
}
