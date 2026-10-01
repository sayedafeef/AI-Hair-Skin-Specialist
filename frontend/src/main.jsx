import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Navigate, NavLink, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthContext.jsx'
import ConsultationPage from './ConsultationPage.jsx'
import HistoryPage from './HistoryPage.jsx'
import LoginPage from './LoginPage.jsx'
import './styles.css'

function ProtectedRoute({ children }) {
  const { token, ready } = useAuth()
  if (!ready) return null
  if (!token) return <Navigate to="/login" replace />
  return children
}

function Layout({ children }) {
  const { user, logout } = useAuth()

  return (
    <div className="app-shell">
      <header className="topbar">
        <span className="wordmark">Aurel</span>
        <nav className="specialty-switch">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            Skin
          </NavLink>
          <NavLink to="/hair" className={({ isActive }) => (isActive ? 'active' : '')}>
            Hair
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => (isActive ? 'active' : '')}>
            History
          </NavLink>
        </nav>
        {user && (
          <div className="account-controls">
            <span className="account-email">{user.email}</span>
            <button type="button" className="link-button" onClick={logout}>
              Log out
            </button>
          </div>
        )}
      </header>
      <main>{children}</main>
    </div>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <ConsultationPage
                pageTitle="Skin consultation"
                pageDescription="Describe what you're noticing on your skin and add a clear, well-lit photo. A coordinator agent reads both before choosing which specialist responds."
                mediaLabel="Skin image"
              />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/hair"
        element={
          <ProtectedRoute>
            <Layout>
              <ConsultationPage
                pageTitle="Hair and scalp consultation"
                pageDescription="Describe what's happening with your hair or scalp and add a clear photo. The same coordinator agent reads both before choosing which specialist responds."
                mediaLabel="Hair or scalp image"
              />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <Layout>
              <HistoryPage />
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
