import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './context/AuthContext'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import Trading from './pages/Trading'
import Profile from './pages/Profile'

function HomeRedirect() {
  const { user } = useAuth()
  return <Navigate to={user ? '/dashboard' : '/landing'} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/landing" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
          />
          <Route
            path="/portfolio"
            element={<ProtectedRoute><Portfolio /></ProtectedRoute>}
          />
          <Route
            path="/trading"
            element={<ProtectedRoute><Trading /></ProtectedRoute>}
          />
          <Route
            path="/profile"
            element={<ProtectedRoute><Profile /></ProtectedRoute>}
          />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
