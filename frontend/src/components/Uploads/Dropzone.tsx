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
        className={['dropzone', 'dropzone--compact', dragActive ? 'dropzone--active' : ''].join(' ')}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <img
              src={preview}
              alt="Preview"
              className="dropzone-preview dropzone-preview--thumbnail"
            />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              ✓ Image uploaded
            </span>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <label htmlFor={inputId} className="button" style={{ fontSize: '0.85rem', padding: '0.6rem 1rem' }}>
              📷 Upload image
            </label>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              or drag and drop (max {Math.round(maxSize / (1024 * 1024))}MB)
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
