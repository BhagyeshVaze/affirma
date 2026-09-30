// Fetch wrapper for our backend. Turns our error shape into an ApiError.

export class ApiError extends Error {
  constructor(code, message, retryAfterS = null, status = null) {
    super(message)
    this.code = code
    this.retryAfterS = retryAfterS
    this.status = status
  }
}

export async function getJson(path, params, signal) {
  const url = `${path}?${new URLSearchParams(params)}`
  let resp
  try {
    resp = await fetch(url, { signal })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new ApiError('network_error', "Can't reach the backend. Is it running on port 8000?")
  }

  let body = null
  try {
    body = await resp.json()
  } catch {
    // not JSON: usually the dev proxy saying the backend is down
  }
  if (!resp.ok) {
    const e = body?.error
    if (!e) throw new ApiError('network_error', "Can't reach the backend. Is it running on port 8000?", null, resp.status)
    throw new ApiError(e.code, e.message, e.retry_after_s, resp.status)
  }
  return body
}
