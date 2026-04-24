import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await login(form.username, form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <p className="eyebrow">Welcome back</p>
        <h2>Login to your account</h2>
        <input placeholder="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
        <div className="password-field">
          <input
            type={showPassword ? 'text' : 'password'}
            placeholder="Password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          <button
            type="button"
            className="password-toggle"
            onClick={() => setShowPassword((current) => !current)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? '🙈' : '👁'}
          </button>
        </div>
        {error && <div className="error-box">{error}</div>}
        <button className="button button-primary" type="submit">Login</button>
        <p className="form-link">No account yet? <Link to="/register">Register</Link></p>
      </form>
    </main>
  )
}
