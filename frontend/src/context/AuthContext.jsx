import { createContext, useContext, useEffect, useState } from 'react'
import client from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('4m_gold_ai_token')
    const storedUser = localStorage.getItem('4m_gold_ai_user')
    if (token && storedUser) {
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const { data } = await client.post('/auth/login', { username, password })
    localStorage.setItem('4m_gold_ai_token', data.access_token)
    localStorage.setItem('4m_gold_ai_user', JSON.stringify(data.user))
    setUser(data.user)
  }

  const register = async (payload) => {
    const { data } = await client.post('/auth/register', payload)
    localStorage.setItem('4m_gold_ai_token', data.access_token)
    localStorage.setItem('4m_gold_ai_user', JSON.stringify(data.user))
    setUser(data.user)
  }

  const logout = () => {
    localStorage.removeItem('4m_gold_ai_token')
    localStorage.removeItem('4m_gold_ai_user')
    setUser(null)
  }

  const deleteAccount = async () => {
    await client.delete('/auth/me')
    logout()
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, deleteAccount }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
