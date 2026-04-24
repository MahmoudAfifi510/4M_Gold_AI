import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'

function formatDateTime(value) {
  if (!value) return 'N/A'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return 'N/A'
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(parsed)
}

export default function Profile() {
  const { user, logout, deleteAccount } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(user)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [clearing, setClearing] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await client.get('/auth/me')
        setProfile(data)
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load profile')
      }
    }
    load()
  }, [])

  const handleClearData = async () => {
    const confirmed = window.confirm(
      'Clear your portfolio data? This will remove all buy and sell transactions and reset your profit history.'
    )
    if (!confirmed) return

    setError('')
    setMessage('')
    setClearing(true)
    try {
      await client.delete('/portfolio/data')
      setMessage('Your portfolio data was cleared successfully.')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not clear account data')
    } finally {
      setClearing(false)
    }
  }

  const handleDeleteAccount = async () => {
    const confirmed = window.confirm(
      'Delete your account permanently? This will remove your profile, portfolio data, and all related history.'
    )
    if (!confirmed) return

    setError('')
    setMessage('')
    setDeleting(true)
    try {
      await deleteAccount()
      logout()
      navigate('/login')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not delete account')
    } finally {
      setDeleting(false)
    }
  }

  const details = profile || user

  return (
    <main className="content-grid">
      <section className="panel panel-wide">
        <div className="section-head">
          <div>
            <p className="eyebrow">Profile</p>
            <h2>Your account details</h2>
          </div>
        </div>

        {error && <div className="error-box">{error}</div>}
        {message && <div className="success-box">{message}</div>}

        {details && (
          <div className="profile-card">
            <div className="profile-grid">
              <div>
                <span className="chart-label">First name</span>
                <strong>{details.first_name}</strong>
              </div>
              <div>
                <span className="chart-label">Last name</span>
                <strong>{details.last_name}</strong>
              </div>
              <div>
                <span className="chart-label">Username</span>
                <strong>{details.username}</strong>
              </div>
              <div>
                <span className="chart-label">Phone</span>
                <strong>{details.phone_number}</strong>
              </div>
              <div>
                <span className="chart-label">User ID</span>
                <strong>{details.id}</strong>
              </div>
              <div>
                <span className="chart-label">Created at</span>
                <strong>{formatDateTime(details.created_at)}</strong>
              </div>
            </div>
          </div>
        )}

        <div className="danger-zone">
          <div>
            <p className="eyebrow">Account actions</p>
            <h3>Clear or delete your account</h3>
            <p className="muted">
              Clear data resets your transactions and profit history. Delete account removes your profile entirely.
            </p>
          </div>
          <div className="profile-actions">
            <button className="button button-secondary" type="button" onClick={handleClearData} disabled={clearing}>
              {clearing ? 'Clearing...' : 'Clear account data'}
            </button>
            <button className="button button-danger" type="button" onClick={handleDeleteAccount} disabled={deleting}>
              {deleting ? 'Deleting...' : 'Delete account'}
            </button>
          </div>
        </div>
      </section>
    </main>
  )
}
