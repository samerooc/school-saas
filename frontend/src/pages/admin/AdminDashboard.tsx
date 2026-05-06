import { Routes, Route, NavLink } from 'react-router-dom'
import { useState, lazy, Suspense } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { GraduationCap, IndianRupee, Bell, Menu, X, LayoutDashboard, UserCog, ClipboardList, Video, Settings, LogOut, BookOpen, BarChart2, MessageCircle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
const StudentsPage = lazy(() => import('./StudentsPage'))
const ReportsPage  = lazy(() => import('./ReportsPage'))
const ChatPage     = lazy(() => import('@/pages/shared/ChatPage'))

const nav = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/admin' },
  { icon: GraduationCap,   label: 'Students',  to: '/admin/students' },
  { icon: UserCog,         label: 'Staff',     to: '/admin/staff' },
  { icon: IndianRupee,     label: 'Fees',      to: '/admin/fees' },
  { icon: ClipboardList,   label: 'Attendance',to: '/admin/attendance' },
  { icon: BookOpen,        label: 'Classes',   to: '/admin/classes' },
  { icon: Video,           label: 'Videos',    to: '/admin/videos' },
  { icon: Bell,            label: 'Notices',   to: '/admin/notices' },
  { icon: BarChart2,       label: 'Reports',   to: '/admin/reports' },
  { icon: MessageCircle,   label: 'Chat',      to: '/admin/chat' },
  { icon: Settings,        label: 'Settings',  to: '/admin/settings' },
]

function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, logout } = useAuthStore()
  return (
    <>
      {open && <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={onClose} />}
      <aside className={`fixed left-0 top-0 h-full w-60 bg-gray-900 border-r border-gray-800 z-30 flex flex-col transition-transform duration-300 ${open?'translate-x-0':'-translate-x-full'} lg:translate-x-0`}>
        <div className="flex items-center gap-3 p-4 border-b border-gray-800">
          <div className="w-8 h-8 bg-indigo-600 rounded-xl flex items-center justify-center"><GraduationCap size={16} className="text-white"/></div>
          <div className="flex-1"><p className="text-white font-bold text-sm">SchoolSaaS</p><p className="text-gray-500 text-xs capitalize">{user?.role} Portal</p></div>
          <button onClick={onClose} className="text-gray-500 lg:hidden"><X size={16}/></button>
        </div>
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          {nav.map(({ icon: Icon, label, to }) => (
            <NavLink key={to} to={to} end={to==='/admin'}
              className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition ${isActive?'bg-indigo-600 text-white':'text-gray-400 hover:bg-gray-800 hover:text-white'}`}
              onClick={onClose}><Icon size={15}/>{label}</NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-800">
          <div className="flex items-center gap-2.5 mb-2.5">
            <div className="w-7 h-7 bg-indigo-600 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0">{user?.full_name?.charAt(0)}</div>
            <div className="flex-1 min-w-0"><p className="text-white text-xs font-medium truncate">{user?.full_name}</p><p className="text-gray-500 text-xs capitalize">{user?.role}</p></div>
          </div>
          <button onClick={logout} className="w-full flex items-center gap-2 px-3 py-1.5 rounded-xl text-red-400 hover:bg-red-400/10 transition text-xs"><LogOut size={13}/>Sign out</button>
        </div>
      </aside>
    </>
  )
}

function DashboardHome() {
  const att = [{day:'Mon',v:92},{day:'Tue',v:88},{day:'Wed',v:95},{day:'Thu',v:91},{day:'Fri',v:87},{day:'Sat',v:78}]
  const fee = [{m:'Jan',v:240000},{m:'Feb',v:180000},{m:'Mar',v:310000},{m:'Apr',v:290000}]
  return (
    <div className="space-y-5">
      <div><h1 className="text-white text-xl font-bold">Dashboard</h1><p className="text-gray-400 text-sm">Today's overview</p></div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[{icon:GraduationCap,l:'Students',v:'1,248',s:'↑ 12 this month',c:'bg-indigo-600'},
          {icon:UserCog,l:'Staff',v:'64',s:'2 new joined',c:'bg-violet-600'},
          {icon:IndianRupee,l:'Fee Collected',v:'₹3.1L',s:'↑ 18% vs last',c:'bg-emerald-600'},
          {icon:ClipboardList,l:'Attendance',v:'91%',s:'↑ 3% vs last week',c:'bg-amber-600'}
        ].map(({icon:Icon,l,v,s,c}) => (
          <div key={l} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
            <div className={`w-9 h-9 ${c} rounded-xl flex items-center justify-center mb-3`}><Icon size={16} className="text-white"/></div>
            <p className="text-white text-xl font-bold">{v}</p>
            <p className="text-gray-400 text-xs mt-0.5">{l}</p>
            <p className="text-green-400 text-xs mt-1.5">{s}</p>
          </div>
        ))}
      </div>
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
          <h3 className="text-white font-semibold text-sm mb-4">Attendance This Week</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={att} barSize={24}><XAxis dataKey="day" tick={{fill:'#6b7280',fontSize:11}} axisLine={false} tickLine={false}/><YAxis tick={{fill:'#6b7280',fontSize:11}} axisLine={false} tickLine={false} domain={[70,100]}/><Tooltip contentStyle={{backgroundColor:'#111827',border:'1px solid #374151',borderRadius:8}}/><Bar dataKey="v" fill="#4f46e5" radius={[5,5,0,0]} name="%"/></BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
          <h3 className="text-white font-semibold text-sm mb-4">Fee Collection</h3>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={fee}><XAxis dataKey="m" tick={{fill:'#6b7280',fontSize:11}} axisLine={false} tickLine={false}/><YAxis tick={{fill:'#6b7280',fontSize:11}} axisLine={false} tickLine={false} tickFormatter={v=>`₹${(v/1000).toFixed(0)}k`}/><Tooltip contentStyle={{backgroundColor:'#111827',border:'1px solid #374151',borderRadius:8}} formatter={(v:number)=>[`₹${v.toLocaleString()}`,'Collected']}/><Line dataKey="v" stroke="#10b981" strokeWidth={2} dot={{fill:'#10b981',r:3}}/></LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
        <h3 className="text-white font-semibold text-sm mb-3">Quick Actions</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[['Add Student','/admin/students','bg-indigo-600'],['Collect Fee','/admin/fees','bg-emerald-600'],['View Reports','/admin/reports','bg-amber-600'],['Chat','/admin/chat','bg-violet-600']].map(([l,h,c])=>(
            <a key={l as string} href={h as string} className={`${c} text-white text-xs font-medium px-3 py-2.5 rounded-xl hover:opacity-90 transition text-center`}>{l}</a>
          ))}
        </div>
      </div>
    </div>
  )
}

function CS({ label }: { label: string }) {
  return <div className="flex items-center justify-center min-h-[50vh]"><div className="text-center"><div className="text-4xl mb-3">🚧</div><h2 className="text-white text-lg font-bold">{label}</h2><p className="text-gray-400 text-sm mt-1">Coming soon</p></div></div>
}
function Spin() { return <div className="flex justify-center h-48 items-center"><div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"/></div> }

export default function AdminDashboard() {
  const [open, setOpen] = useState(false)
  return (
    <div className="min-h-screen bg-gray-950 lg:pl-60">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <header className="sticky top-0 z-10 bg-gray-950/80 backdrop-blur border-b border-gray-800 px-4 py-3 flex items-center gap-3">
        <button onClick={() => setOpen(true)} className="text-gray-400 lg:hidden"><Menu size={20}/></button>
        <div className="flex-1"/>
        <button className="relative text-gray-400 hover:text-white"><Bell size={18}/><span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-red-500 rounded-full text-white text-[9px] flex items-center justify-center">3</span></button>
      </header>
      <main className="p-4 lg:p-5">
        <Suspense fallback={<Spin/>}>
          <Routes>
            <Route index              element={<DashboardHome/>}/>
            <Route path="students/*"  element={<StudentsPage/>}/>
            <Route path="staff"       element={<CS label="Staff Management"/>}/>
            <Route path="fees"        element={<CS label="Fee Management"/>}/>
            <Route path="attendance"  element={<CS label="Attendance"/>}/>
            <Route path="classes"     element={<CS label="Classes & Subjects"/>}/>
            <Route path="videos"      element={<CS label="Video LMS"/>}/>
            <Route path="notices"     element={<CS label="Notices"/>}/>
            <Route path="reports"     element={<ReportsPage/>}/>
            <Route path="chat"        element={<ChatPage/>}/>
            <Route path="settings"    element={<CS label="Settings"/>}/>
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}
