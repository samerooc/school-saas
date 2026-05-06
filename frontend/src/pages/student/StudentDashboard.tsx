import { Routes, Route, NavLink } from 'react-router-dom'
import { useState } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { LayoutDashboard, Play, ClipboardList, IndianRupee, Bell, LogOut, Menu, X, GraduationCap } from 'lucide-react'
import { lazy, Suspense } from 'react'
const StudentVideosPage = lazy(() => import('./StudentVideosPage'))

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/student' },
  { icon: Play,            label: 'My Videos', to: '/student/videos' },
  { icon: ClipboardList,   label: 'Attendance', to: '/student/attendance' },
  { icon: IndianRupee,     label: 'Fees',       to: '/student/fees' },
  { icon: Bell,            label: 'Notices',    to: '/student/notices' },
]

function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, logout } = useAuthStore()
  return (
    <>
      {open && <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={onClose} />}
      <aside className={`fixed left-0 top-0 h-full w-60 bg-gray-900 border-r border-gray-800 z-30 flex flex-col transition-transform duration-300 ${open ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}>
        <div className="flex items-center gap-3 p-4 border-b border-gray-800">
          <div className="w-8 h-8 bg-emerald-600 rounded-xl flex items-center justify-center"><GraduationCap size={16} className="text-white" /></div>
          <div className="flex-1"><p className="text-white font-bold text-sm">SchoolSaaS</p><p className="text-gray-500 text-xs">Student Portal</p></div>
          <button onClick={onClose} className="text-gray-500 lg:hidden"><X size={16} /></button>
        </div>
        <nav className="flex-1 p-2 space-y-0.5">
          {navItems.map(({ icon: Icon, label, to }) => (
            <NavLink key={to} to={to} end={to === '/student'}
              className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition ${isActive ? 'bg-emerald-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'}`}
              onClick={onClose}
            ><Icon size={15} />{label}</NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-800">
          <div className="flex items-center gap-2.5 mb-2.5">
            <div className="w-7 h-7 bg-emerald-600 rounded-full flex items-center justify-center text-white text-xs font-bold">{user?.full_name?.charAt(0)}</div>
            <div className="flex-1 min-w-0"><p className="text-white text-xs font-medium truncate">{user?.full_name}</p><p className="text-gray-500 text-xs">Student</p></div>
          </div>
          <button onClick={logout} className="w-full flex items-center gap-2 px-3 py-1.5 rounded-xl text-red-400 hover:bg-red-400/10 transition text-xs"><LogOut size={13} />Sign out</button>
        </div>
      </aside>
    </>
  )
}

function StudentHome() {
  const { user } = useAuthStore()
  return (
    <div className="space-y-5">
      <div><h1 className="text-white text-xl font-bold">Welcome, {user?.full_name?.split(' ')[0]}!</h1><p className="text-gray-400 text-sm">Your learning dashboard</p></div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[['🎬', 'My Videos', '/student/videos'], ['📋', 'Attendance', '/student/attendance'], ['💰', 'Fee Status', '/student/fees'], ['📢', 'Notices', '/student/notices']].map(([emoji, label, href]) => (
          <a key={label as string} href={href as string} className="bg-gray-900 border border-gray-800 rounded-2xl p-5 text-center hover:border-emerald-500 transition">
            <div className="text-2xl mb-2">{emoji}</div>
            <p className="text-white text-sm font-medium">{label}</p>
          </a>
        ))}
      </div>
    </div>
  )
}

function ComingSoon({ label }: { label: string }) {
  return <div className="flex items-center justify-center min-h-[50vh]"><div className="text-center"><div className="text-4xl mb-3">🚧</div><h2 className="text-white text-lg font-bold">{label}</h2></div></div>
}

export default function StudentDashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  return (
    <div className="min-h-screen bg-gray-950 lg:pl-60">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <header className="sticky top-0 z-10 bg-gray-950/80 backdrop-blur border-b border-gray-800 px-4 py-3 flex items-center">
        <button onClick={() => setSidebarOpen(true)} className="text-gray-400 lg:hidden"><Menu size={20} /></button>
      </header>
      <main className="p-4 lg:p-5">
        <Suspense fallback={<div className="flex justify-center h-48 items-center"><div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>}>
          <Routes>
            <Route index        element={<StudentHome />} />
            <Route path="videos" element={<StudentVideosPage />} />
            <Route path="attendance" element={<ComingSoon label="Attendance" />} />
            <Route path="fees"       element={<ComingSoon label="Fee Status" />} />
            <Route path="notices"    element={<ComingSoon label="Notices" />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}
