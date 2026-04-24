import axios from 'axios'

const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')

const client = axios.create({
  baseURL: apiBaseUrl
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('4m_gold_ai_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default client
