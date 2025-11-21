import React, { useState, useId } from 'react'

interface FileUploadZoneProps {
  onUpload: (file: File) => void
  accept: string
  maxSize: number
}


export const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onUpload,
  accept,
  maxSize
}) => {
  const [dragActive, setDragActive] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const inputId = useId()

  const handleFile = (file: File) => {
    if (!file) return

    if (file.size > maxSize) {
      alert('The selected file is too large. Please choose a smaller image.')
      return
    }

    const reader = new FileReader()
    reader.onload = (event) => {
      if (event.target?.result) {
        setPreview(event.target.result as string)
      }
    }
    reader.readAsDataURL(file)
    onUpload(file)
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragActive(false)
    const droppedFile = event.dataTransfer.files?.[0]
    if (droppedFile) {
      handleFile(droppedFile)
    }
  }

  return (
    <div>
      <input
        id={inputId}
        type="file"
        accept={accept}
        style={{ display: 'none' }}
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) {
            handleFile(file)
          }
        }}
      />
      <div
        className={['dropzone', dragActive ? 'dropzone--active' : ''].join(' ')}
        onDragEnter={(event) => {
          event.preventDefault()
          setDragActive(true)
        }}
        onDragLeave={(event) => {
          event.preventDefault()
          setDragActive(false)
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        {preview ? (
          <img
            src={preview}
            alt="Uploaded item preview"
            className="dropzone-preview"
          />
        ) : (
          <>
            <p style={{ marginBottom: '0.5rem', fontWeight: 600 }}>
              Drag and drop a supporting photo
            </p>
            <p style={{ marginBottom: '1rem', color: 'var(--text-muted)' }}>
              JPEG, PNG or WEBP files up to {Math.round(maxSize / (1024 * 1024))}MB
            </p>
            <label htmlFor={inputId} className="button">
              Choose an image
            </label>
          </>
        )}
      </div>
    </div>
  )
}
