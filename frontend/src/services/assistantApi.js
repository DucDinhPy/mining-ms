const configuredBaseUrl = import.meta.env.VITE_ASSISTANT_API_URL?.trim().replace(/\/$/, '')

function buildUrl(path) {
  return configuredBaseUrl ? `${configuredBaseUrl}${path}` : path
}

export async function sendAssistantMessage(payload, { signal } = {}) {
  const response = await fetch(buildUrl('/api/assistant/messages'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    signal,
  })

  let body = null

  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    throw new Error(
      body?.detail
      || body?.message
      || `Assistant request failed (${response.status}).`,
    )
  }

  return body
}
