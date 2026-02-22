import { useState, useEffect, useCallback } from 'react'

export interface User {
  entra_id: string
  email: string
  display_name: string
  platform_role: string
  groups: string[]
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch('/auth/me', { credentials: 'include' })
      const data = await res.json()
      if (data.authenticated && data.user) {
        setUser(data.user)
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = useCallback(() => {
    window.location.href = '/auth/login?returnTo=' + encodeURIComponent(window.location.pathname)
  }, [])

  const logout = useCallback(() => {
    window.location.href = '/auth/logout'
  }, [])

  return { user, loading, login, logout, isAuthenticated: !!user }
}
