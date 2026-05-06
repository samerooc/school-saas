import { useEffect, lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/authStore'
import { PrivateRoute, RoleGuard } from '@/components/auth/Guards'
import LoginPage from '@/pages/auth/LoginPage'

const AdminDashboard   = lazy(() => import('@/pages/admin/AdminDashboard'))
const TeacherDashboard = lazy(() => import('@/pages/teacher/TeacherDashboard'))
const StudentDashboard = lazy(() => import('@/pages/student/StudentDashboard'))
const ParentDashboard  = lazy(() => import('@/pages/parent/ParentDashboard'))
const PublicWebsite    = lazy(() => import('@/pages/public/PublicWebsite'))

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 5 * 60 * 1000 } },
})

function Spin() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function AppRoutes() {
  const { refreshToken } = useAuthStore()
  useEffect(() => { refreshToken() }, [])
  return (
    <Suspense fallback={<Spin />}>
      <Routes>
        <Route path="/"         element={<PublicWebsite />} />
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/admin/*"   element={<PrivateRoute><RoleGuard allowedRoles={['admin','principal']}><AdminDashboard /></RoleGuard></PrivateRoute>} />
        <Route path="/staff/*"   element={<PrivateRoute><RoleGuard allowedRoles={['teacher']}><TeacherDashboard /></RoleGuard></PrivateRoute>} />
        <Route path="/student/*" element={<PrivateRoute><RoleGuard allowedRoles={['student']}><StudentDashboard /></RoleGuard></PrivateRoute>} />
        <Route path="/parent/*"  element={<PrivateRoute><RoleGuard allowedRoles={['parent']}><ParentDashboard /></RoleGuard></PrivateRoute>} />
        <Route path="*" element={
          <div className="min-h-screen flex items-center justify-center bg-gray-950">
            <div className="text-center">
              <p className="text-8xl font-bold text-indigo-500">404</p>
              <h2 className="text-white text-2xl font-bold mt-4">Page Not Found</h2>
              <a href="/" className="mt-6 inline-block bg-indigo-600 text-white px-6 py-2 rounded-xl hover:bg-indigo-500 transition">Go Home</a>
            </div>
          </div>
        } />
      </Routes>
    </Suspense>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
