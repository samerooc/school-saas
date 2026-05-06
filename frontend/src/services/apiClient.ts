/**
 * Axios instance with:
 * 1. Auto-attach Bearer token
 * 2. 401 → silent refresh → retry original request
 * 3. Refresh fails → redirect to login
 */
import axios, { AxiosRequestConfig } from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true,  // Send HttpOnly cookie with every request
  headers: { 'X-Requested-With': 'XMLHttpRequest' }, // CSRF hint
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token!)
  })
  failedQueue = []
}

// Response interceptor — handle 401 silently
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !original._retry && !original.url?.includes('/auth/')) {
      if (isRefreshing) {
        // Queue this request while refresh is in progress
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          original.headers = { ...original.headers, Authorization: `Bearer ${token}` }
          return apiClient(original)
        })
      }

      original._retry = true
      isRefreshing = true

      try {
        const res = await apiClient.post('/auth/refresh')
        const newToken = res.data.access_token
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
        processQueue(null, newToken)
        original.headers = { ...original.headers, Authorization: `Bearer ${newToken}` }
        return apiClient(original)
      } catch (refreshError) {
        processQueue(refreshError, null)
        // Refresh failed — clear auth and redirect
        delete apiClient.defaults.headers.common['Authorization']
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)
