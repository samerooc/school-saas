import { Routes, Route, NavLink } from 'react-router-dom'
import { useState, lazy, Suspense } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { LayoutDashboard, TrendingUp, IndianRupee, Bell, LogOut, Menu, X, GraduationCap, MessageCircle } from 'lucide-react'
const ChatPage = lazy(() => import('@/pages/shared/ChatPage'))

const nav = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/parent' },
  { icon: TrendingUp,      label: 'Progress',  to: '/parent/progress' },
  { icon: IndianRupee,     label: 'Fees',      to: '/parent/fees' },
  { icon: MessageCircle,   label: 'Chat',      to: '/parent/chat' },
  { icon: Bell,            label: 'Notices',   to: '/parent/notices' },
]

function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, logout } = useAuthStore()
  return (
    <>
      {open && <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={onClose}/>}
      <aside className={`fixed left-0 top-0 h-full w-60 bg-gray-900 border-r border-gray-800 z-30 flex flex-col transition-transform duration-300 ${open?'translate-x-0':'-translate-x-full'} lg:translate-x-0`}>
        <div className="flex items-center gap-3 p-4 border-b border-gray-800">
          <div className="w-8 h-8 bg-emerald-600 rounded-xl flex items-center justify-center"><GraduationCap size={16} className="text-white"/></div>
          <div className="flex-1"><p className="text-white font-bold text-sm">SchoolSaaS</p><p className="text-gray-500 text-xs">Parent Portal</p></div>
          <button onClick={onClose} className="text-gray-500 lg:hidden"><X size={16}/></button>
        </div>
        <nav className="flex-1 p-2 space-y-0.5">
          {nav.map(({ icon: Icon, label, to }) => (
            <NavLink key={to} to={to} end={to==='/parent'}
              className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition ${isActive?'bg-emerald-600 text-white':'text-gray-400 hover:bg-gray-800 hover:text-white'}`}
              onClick={onClose}><Icon size={15}/>{label}</NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-800">
          <div className="flex items-center gap-2.5 mb-2.5">
            <div className="w-7 h-7 bg-emerald-600 rounded-full flex items-center justify-center text-white text-xs font-bold">{user?.full_name?.charAt(0)}</div>
            <div className="flex-1 min-w-0"><p className="text-white text-xs font-medium truncate">{user?.full_name}</p><p className="text-gray-500 text-xs">Parent</p></div>
          </div>
          <button onClick={logout} className="w-full flex items-center gap-2 px-3 py-1.5 rounded-xl text-red-400 hover:bg-red-400/10 transition text-xs"><LogOut size={13}/>Sign out</button>
        </div>
      </aside>
    </>
  )
}

function ParentHome() {
  const { user } = useAuthStore()
  return (
    <div className="space-y-5">
      <div><h1 className="text-white text-xl font-bold">Welcome, {user?.full_name?.split(' ')[0]}!</h1><p className="text-gray-400 text-sm">Your child's learning overview</p></div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[['📈',"Child's Progress",'/parent/progress'],['💰','Pay Fees','/parent/fees'],['💬','Chat Teacher','/parent/chat'],['📢','Notices','/parent/notices']].map(([emoji,label,href]) => (
          <a key={label as string} href={href as string} className="bg-gray-900 border border-gray-800 rounded-2xl p-5 text-center hover:border-emerald-500 transition">
            <div className="text-2xl mb-2">{emoji}</div>
            <p className="text-white text-sm font-medium">{label}</p>
          </a>
        ))}
      </div>
    </div>
  )
}

function CS({ label }: { label: string }) {
  return <div className="flex items-center justify-center min-h-[50vh]"><div className="text-center"><div className="text-4xl mb-3">🚧</div><h2 className="text-white text-lg font-bold">{label}</h2></div></div>
}
function Spin() { return <div className="flex justify-center h-48 items-center"><div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"/></div> }

export default function ParentDashboard() {
  const [open, setOpen] = useState(false)
  return (
    <div className="min-h-screen bg-gray-950 lg:pl-60">
      <Sidebar open={open} onClose={() => setOpen(false)}/>
      <header className="sticky top-0 z-10 bg-gray-950/80 backdrop-blur border-b border-gray-800 px-4 py-3 flex items-center">
        <button onClick={() => setOpen(true)} className="text-gray-400 lg:hidden"><Menu size={20}/></button>
      </header>
      <main className="p-4 lg:p-5">
        <Suspense fallback={<Spin/>}>
          <Routes>
            <Route index           element={<ParentHome/>}/>
            <Route path="progress" element={<CS label="Child Progress"/>}/>
            <Route path="fees"     element={<CS label="Fee Payment"/>}/>
            <Route path="chat"     element={<ChatPage/>}/>
            <Route path="notices"  element={<CS label="Notices"/>}/>
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}
