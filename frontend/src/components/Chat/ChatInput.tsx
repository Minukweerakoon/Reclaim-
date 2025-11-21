import React, { useState } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled: boolean
  placeholder?: string
}


export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled,
  placeholder = 'Type your message...'
}) => {
  const [input, setInput] = useState('')

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    const trimmed = input.trim()
    if (trimmed && !disabled) {
      onSend(trimmed)
      setInput('')
    }
  }

  return (
    <form className="chat-input__form" onSubmit={handleSubmit}>
      <input
        className="chat-input__field"
        type="text"
        value={input}
        onChange={(event) => setInput(event.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        aria-label="Chat message"
      />
      <button
        className="button"
        type="submit"
        disabled={disabled || input.trim().length === 0}
      >
        Send
      </button>
    </form>
  )
}
