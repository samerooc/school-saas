/**
 * Auth Store — Zustand
 * ACCESS TOKEN stored in MEMORY only (never localStorage/sessionStorage)
 * WHY: localStorage is readable by any JS — XSS attack vector
 * Refresh token lives in HttpOnly cookie — backend sets/clears it
 */
import { create } from 'zustand'
import { apiClient } from '@/services/apiClient'

interface AuthUser {
  id: string
  full_name: string
  role: 'admin' | 'principal' | 'teacher' | 'student' | 'parent'
  school_id: string
  is_premium?: boolean
}

interface AuthState {
  accessToken: string | null   // In-memory only
  user: AuthUser | null
  isLoading: boolean

  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<boolean>
  setTokenAndUser: (token: string, user: AuthUser) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  user: null,
  isLoading: true,

  setTokenAndUser: (token, user) => {
    set({ accessToken: token, user, isLoading: false })
    // Attach token to all future requests
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  },

  clearAuth: () => {
    set({ accessToken: null, user: null, isLoading: false })
    delete apiClient.defaults.headers.common['Authorization']
  },

  login: async (email, password) => {
    const res = await apiClient.post('/auth/login', { email, password })
    const { access_token, role, user_id, full_name } = res.data
    get().setTokenAndUser(access_token, {
      id: user_id,
      full_name,
      role,
      school_id: '', // Will be in JWT — fetch from /me if needed
    })
  },

  logout: async () => {
    try {
      await apiClient.post('/auth/logout')
    } finally {
      get().clearAuth()
    }
  },

  refreshToken: async () => {
    try {
      // Cookie sent automatically (HttpOnly)
      const res = await apiClient.post('/auth/refresh')
      const { access_token, role, user_id, full_name } = res.data
      get().setTokenAndUser(access_token, { id: user_id, full_name, role, school_id: '' })
      return true
    } catch {
      get().clearAuth()
      return false
    }
  },
}))
