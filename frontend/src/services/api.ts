import { useAppStore } from '../state/store'

export async function postText(text: string, language: string = 'auto') {
  const { api } = useAppStore.getState()
  const res = await fetch(`${api!.baseUrl}/validate/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': api!.apiKey },
    body: JSON.stringify({ text, language })
  })
  if (!res.ok) throw new Error(`Text validation failed: ${res.status}`)
  return res.json()
}

export async function postImage(file: File, text?: string) {
  const { api } = useAppStore.getState()
  const form = new FormData()
  form.append('image_file', file)
  if (text) form.append('text', text)
  const res = await fetch(`${api!.baseUrl}/validate/image`, {
    method: 'POST',
    headers: { 'X-API-Key': api!.apiKey },
    body: form
  })
  if (!res.ok) throw new Error(`Image validation failed: ${res.status}`)
  return res.json()
}

export async function postAudio(file: File) {
  const { api } = useAppStore.getState()
  const form = new FormData()
  form.append('audio_file', file)
  const res = await fetch(`${api!.baseUrl}/validate/voice`, {
    method: 'POST',
    headers: { 'X-API-Key': api!.apiKey },
    body: form
  })
  if (!res.ok) throw new Error(`Audio validation failed: ${res.status}`)
  return res.json()
}

export function getWsUrl(clientId: string) {
  const { api } = useAppStore.getState()
  const url = new URL(api!.baseUrl)
  const scheme = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${scheme}//${url.host}/ws/validation/${clientId}`
}

