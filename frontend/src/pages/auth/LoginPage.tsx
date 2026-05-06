import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Eye, EyeOff, GraduationCap, Loader2, AlertCircle } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

const schema = z.object({
  email: z.string().email('Valid email required'),
  password: z.string().min(1, 'Password required'),
})
type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const login = useAuthStore((s) => s.login)
  const user = useAuthStore((s) => s.user)
  const [showPwd, setShowPwd] = useState(false)
  const [serverError, setServerError] = useState('')

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const ROLE_ROUTES: Record<string, string> = {
    admin: '/admin',
    principal: '/principal',
    teacher: '/staff',
    student: '/student',
    parent: '/parent',
  }

  const onSubmit = async (data: FormData) => {
    setServerError('')
    try {
      await login(data.email, data.password)
      const from = (location.state as any)?.from?.pathname
      const dest = from || ROLE_ROUTES[useAuthStore.getState().user?.role || ''] || '/'
      navigate(dest, { replace: true })
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Login failed. Please try again.'
      setServerError(msg)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      {/* Background grid */}
      <div className="absolute inset-0 opacity-10"
        style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />

      <div className="relative w-full max-w-md">
        {/* Card */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl">

          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-indigo-500 rounded-2xl flex items-center justify-center shadow-lg">
              <GraduationCap className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-white font-bold text-xl tracking-tight">SchoolSaaS</h1>
              <p className="text-indigo-300 text-sm">Education Platform</p>
            </div>
          </div>

          <h2 className="text-white text-2xl font-bold mb-1">Welcome back</h2>
          <p className="text-indigo-300 text-sm mb-8">Sign in to your portal</p>

          {/* Error alert */}
          {serverError && (
            <div className="flex items-center gap-2 bg-red-500/20 border border-red-400/30 rounded-xl p-3 mb-5">
              <AlertCircle size={16} className="text-red-400 shrink-0" />
              <p className="text-red-300 text-sm">{serverError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-indigo-200 text-sm font-medium mb-1.5">Email</label>
              <input
                type="email"
                autoComplete="email"
                {...register('email')}
                placeholder="you@school.com"
                className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-indigo-400
                           focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition"
              />
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>

            {/* Password */}
            <div>
              <div className="flex justify-between mb-1.5">
                <label className="text-indigo-200 text-sm font-medium">Password</label>
                <a href="/forgot-password" className="text-indigo-400 text-xs hover:text-indigo-300 transition">
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <input
                  type={showPwd ? 'text' : 'password'}
                  autoComplete="current-password"
                  {...register('password')}
                  placeholder="••••••••"
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 pr-12 text-white placeholder-indigo-400
                             focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-indigo-400 hover:text-indigo-200 transition"
                >
                  {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-indigo-500 hover:bg-indigo-400 disabled:opacity-60 disabled:cursor-not-allowed
                         text-white font-semibold py-3 rounded-xl transition-all duration-200
                         flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/30"
            >
              {isSubmitting ? (
                <><Loader2 size={18} className="animate-spin" /> Signing in...</>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Role hint */}
          <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
            <p className="text-indigo-300 text-xs text-center">
              Use your school-provided credentials.
              Different roles (Admin, Teacher, Student, Parent) use the same login.
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-indigo-400 text-xs mt-4">
          © 2025 SchoolSaaS · Secure Education Platform
        </p>
      </div>
    </div>
  )
}
