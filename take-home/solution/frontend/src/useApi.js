import { useCallback, useEffect, useState } from 'react'
import { getJson } from './api.js'

// status: idle | loading | success | error. Pass params = null to stay idle.
// A new request aborts the previous one, so a slow old response can't overwrite a new one.
export function useApi(path, params) {
  const key = params ? JSON.stringify(params) : null
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState({ status: 'idle', data: null, error: null })

  useEffect(() => {
    if (!key) {
      setState({ status: 'idle', data: null, error: null })
      return
    }
    const controller = new AbortController()
    setState({ status: 'loading', data: null, error: null })
    getJson(path, JSON.parse(key), controller.signal).then(
      (data) => setState({ status: 'success', data, error: null }),
      (error) => {
        if (error.name !== 'AbortError') setState({ status: 'error', data: null, error })
      },
    )
    return () => controller.abort()
  }, [path, key, attempt])

  const retry = useCallback(() => setAttempt((n) => n + 1), [])
  return { ...state, retry }
}
