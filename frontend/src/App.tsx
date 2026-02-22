import { Routes, Route, Navigate } from 'react-router-dom'
import { PlatformShell } from '@acture/ui'
import type { PlatformUser } from '@acture/ui'
import { useAuth } from './hooks/useAuth'
import Chat from './pages/Chat'
import Admin from './pages/Admin'
import Feedback from './pages/Feedback'
import Documents from './pages/Documents'

function App() {
  const { user, loading, login, logout, isAuthenticated } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-acture-surface">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-acture-primary" />
      </div>
    )
  }

  if (!isAuthenticated) {
    login()
    return (
      <div className="min-h-screen flex items-center justify-center bg-acture-surface">
        <p className="text-gray-500">Redirecting to sign in...</p>
      </div>
    )
  }

  const platformUser: PlatformUser = {
    displayName: user!.display_name,
    email: user!.email,
    role: user!.platform_role,
    initials: user!.display_name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2),
  }

  return (
    <PlatformShell activeApp="advisor" user={platformUser} onLogout={logout}>
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/admin/feedback" element={<Feedback />} />
        <Route path="/admin/documents" element={<Documents />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </PlatformShell>
  )
}

export default App
