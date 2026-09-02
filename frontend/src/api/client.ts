import axios from 'axios'

const BACKEND_URL = 'https://merchant-revenue-growth-agent.onrender.com'

const client = axios.create({
  baseURL: BACKEND_URL,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (
    !(config.data instanceof FormData) &&
    !(config.data instanceof URLSearchParams)
  ) {
    config.headers['Content-Type'] = 'application/json'
  }
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client
