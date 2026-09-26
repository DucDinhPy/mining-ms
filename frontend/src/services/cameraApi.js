const cameraApiUrl = (import.meta.env.VITE_CAMERA_API_URL || '/api/cameras').replace(/\/$/, '')

async function request(path = '', options = {}) {
  const response = await fetch(`${cameraApiUrl}${path}`, {
    headers: {
      Accept: 'application/json',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
    ...options,
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json()
    : null

  if (!response.ok) {
    const validationErrors = payload?.errors
      ? Object.values(payload.errors).flat().join(' ')
      : ''
    const message = validationErrors
      || payload?.detail
      || payload?.title
      || `Camera API request failed (${response.status}).`
    throw new Error(message)
  }

  return payload
}

export function getCameras({ page = 1, pageSize = 10 } = {}) {
  const query = new URLSearchParams({
    page: String(page),
    pageSize: String(pageSize),
  })
  return request(`?${query}`)
}

export function getCameraById(id) {
  return request(`/${encodeURIComponent(id)}`)
}

export function createCamera(camera) {
  return request('', {
    method: 'POST',
    body: JSON.stringify(camera),
  })
}
