import axios from 'axios'

/**
 * API base URL from environment variable or default to /api for proxy
 * In production, set VITE_API_BASE_URL to your API server URL
 */
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

const client = axios.create({
  baseURL: apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default client

/**
 * Get the static files server URL
 * In production, set VITE_STATIC_URL to your static files server URL
 */
export const getStaticUrl = (path) => {
  const staticBaseUrl = import.meta.env.VITE_STATIC_URL || ''
  if (path && path.startsWith('/')) {
    return `${staticBaseUrl}${path}`
  }
  return path
}
