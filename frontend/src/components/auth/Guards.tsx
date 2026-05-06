import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

// ── Private Route — redirect to login if not authenticated ───────────────────
export function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { accessToken, isLoading } = useAuthStore()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!accessToken) {
    // Save intended destination — redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

// ── Role Guard — 403 if wrong role ───────────────────────────────────────────
export function RoleGuard({
  children,
  allowedRoles,
}: {
  children: React.ReactNode
  allowedRoles: string[]
}) {
  const user = useAuthStore((s) => s.user)

  if (!user) return <Navigate to="/login" replace />

  if (!allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-center">
          <p className="text-8xl font-bold text-indigo-500">403</p>
          <h2 className="text-white text-2xl font-bold mt-4">Access Denied</h2>
          <p className="text-gray-400 mt-2">You don't have permission to view this page.</p>
          <a href="/" className="mt-6 inline-block bg-indigo-600 text-white px-6 py-2 rounded-xl hover:bg-indigo-500 transition">
            Go Home
          </a>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

// ── Premium Guard ─────────────────────────────────────────────────────────────
export function PremiumGuard({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user)

  // Teachers/admins bypass premium check
  if (user?.role && ['teacher', 'admin', 'principal'].includes(user.role)) {
    return <>{children}</>
  }

  if (!user?.is_premium) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-center bg-gradient-to-br from-yellow-500/10 to-orange-500/10
                        border border-yellow-500/20 rounded-2xl p-8 max-w-sm">
          <div className="text-4xl mb-3">⭐</div>
          <h3 className="text-white font-bold text-lg">Premium Content</h3>
          <p className="text-gray-400 text-sm mt-2">
            This content requires premium access. Contact your school admin to unlock.
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
