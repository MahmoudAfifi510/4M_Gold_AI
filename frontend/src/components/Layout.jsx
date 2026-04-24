import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout({ children }) {
  const { user, logout } = useAuth()

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark">4M</span>
          <div>
            <div className="brand-title">4M Gold AI</div>
            <div className="brand-sub">AI trend intelligence</div>
          </div>
        </Link>

        <nav className="nav">
          {user ? (
            <>
              <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : '')}>Dashboard</NavLink>
              <NavLink to="/portfolio" className={({ isActive }) => (isActive ? 'active' : '')}>Portfolio</NavLink>
              <NavLink to="/trading" className={({ isActive }) => (isActive ? 'active' : '')}>Trading</NavLink>
              <NavLink to="/profile" className={({ isActive }) => (isActive ? 'active' : '')}>Profile</NavLink>
              <button className="nav-button" onClick={logout}>Logout</button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={({ isActive }) => (isActive ? 'active' : '')}>Login</NavLink>
              <NavLink to="/register" className={({ isActive }) => (isActive ? 'active' : '')}>Register</NavLink>
            </>
          )}
        </nav>
      </header>
      {children}
    </div>
  )
}
