import { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || ''

export type FetchState<T> = {
  data: T | null
  error: string
  loading: boolean
}

export function useFetch<T>(path: string): FetchState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true

    async function run(): Promise<void> {
      setLoading(true)
      try {
        const payload = await apiRequest<T>(path)
        if (mounted) {
          setData(payload)
          setError('')
        }
      } catch (err) {
        if (mounted) {
          setError(String(err))
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    void run()
    return () => {
      mounted = false
    }
  }, [path])

  return { data, error, loading }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  if (!res.ok) {
    throw new Error(`${path} failed with status ${res.status}`)
  }

  return (await res.json()) as T
}
