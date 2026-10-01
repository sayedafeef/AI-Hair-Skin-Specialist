const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function submitConsultation({ audioBlob, imageFile, videoFile, token }) {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'patient_audio.webm')
  if (imageFile) formData.append('image', imageFile)
  if (videoFile) formData.append('video', videoFile)

  const response = await fetch(`${API_BASE}/api/consult`, {
    method: 'POST',
    headers: authHeaders(token),
    body: formData,
  })

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(detail.detail || `Request failed with status ${response.status}`)
  }

  const data = await response.json()
  return {
    ...data,
    audioUrl: data.audio_url ? `${API_BASE}${data.audio_url}` : null,
  }
}

export async function fetchHistory(token) {
  const response = await fetch(`${API_BASE}/api/history`, {
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(detail.detail || `Request failed with status ${response.status}`)
  }

  const data = await response.json()
  return data.map((r) => ({
    ...r,
    audioUrl: r.audio_url ? `${API_BASE}${r.audio_url}` : null,
  }))
}
