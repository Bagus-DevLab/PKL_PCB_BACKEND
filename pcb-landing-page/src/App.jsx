import { Routes, Route, Navigate } from 'react-router-dom'

// Landing Page components (existing)
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Features from './components/Features'
import Footer from './components/Footer'

// Admin components
import { useAuth } from './admin/hooks/useAuth'
import AdminGuard from './admin/components/AdminGuard'
import AdminLayout from './admin/components/AdminLayout'
import LoginPage from './admin/pages/LoginPage'
import DashboardPage from './admin/pages/DashboardPage'
import UsersPage from './admin/pages/UsersPage'
import DevicesPage from './admin/pages/DevicesPage'

// Landing Page — halaman utama untuk publik
function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-pcb-blue/30 overflow-x-hidden">
      <Navbar />
      <main>
        <Hero />
        <Features />
      </main>
      <Footer />
    </div>
  )
}

function App() {
  const { user, loading, error, login, logout, setError } = useAuth()

  return (
    <Routes>
      {/* Landing Page — publik */}
      <Route path="/" element={<LandingPage />} />

      {/* Admin Login */}
      <Route
        path="/admin/login"
        element={
          user?.role === 'admin' ? (
            <Navigate to="/admin/dashboard" replace />
          ) : (
            <LoginPage
              onLogin={login}
              error={error}
              setError={setError}
              loading={loading}
            />
          )
        }
      />

      {/* Admin Pages — dilindungi AdminGuard */}
      <Route
        path="/admin"
        element={
          <AdminGuard user={user} loading={loading}>
            <AdminLayout user={user} onLogout={logout} />
          </AdminGuard>
        }
      >
        <Route index element={<Navigate to="/admin/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="devices" element={<DevicesPage />} />
      </Route>

      {/* Catch-all — redirect ke landing page */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
