import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, FileSpreadsheet, TrendingUp, Users, IndianRupee, Calendar } from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

function LiveStats() {
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.get('/reports/dashboard/stats').then(r => r.data),
    refetchInterval: 60000,
  })
  if (!stats) return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {[1,2,3,4].map(i => <div key={i} className="bg-gray-900 border border-gray-800 rounded-2xl p-4 animate-pulse h-28"/>)}
    </div>
  )
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          {icon:Users,       label:'Total Students',    value:stats.total_students.toLocaleString(), color:'bg-indigo-600', sub:`${stats.premium_students} premium`},
          {icon:Users,       label:'Staff Members',     value:stats.total_staff.toLocaleString(),    color:'bg-violet-600', sub:'Active'},
          {icon:Calendar,    label:"Today's Attendance",value:`${stats.today_attendance.percentage}%`,color:'bg-emerald-600',sub:`${stats.today_attendance.present}/${stats.today_attendance.total} present`},
          {icon:IndianRupee, label:'This Month Fees',   value:`₹${(stats.fees_this_month/1000).toFixed(1)}k`,color:'bg-amber-600',sub:'Collected'},
        ].map(({icon:Icon,label,value,color,sub}) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
            <div className={`w-9 h-9 ${color} rounded-xl flex items-center justify-center mb-3`}><Icon size={16} className="text-white"/></div>
            <p className="text-white text-xl font-bold">{value}</p>
            <p className="text-gray-400 text-xs mt-0.5">{label}</p>
            <p className="text-gray-500 text-xs mt-1">{sub}</p>
          </div>
        ))}
      </div>
      {stats.attendance_trend && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <h3 className="text-white font-semibold text-sm mb-4 flex items-center gap-2"><TrendingUp size={15} className="text-indigo-400"/> Attendance Trend (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={stats.attendance_trend} barSize={28}>
              <XAxis dataKey="day" tick={{fill:'#6b7280',fontSize:11}} axisLine={false} tickLine={false}/>
              <YAxis domain={[0,100]} tick={{fill:'#6b7280',fontSize:11}} axisLine={false} tickLine={false} tickFormatter={v=>`${v}%`}/>
              <Tooltip contentStyle={{backgroundColor:'#111827',border:'1px solid #374151',borderRadius:8}} formatter={(v:number) => [`${v}%`,'Attendance']}/>
              <Bar dataKey="percentage" fill="#4f46e5" radius={[5,5,0,0]} name="Attendance %"/>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

function ExportReports() {
  const {data:classes} = useQuery({queryKey:['classes'],queryFn:()=>apiClient.get('/classes').then(r=>r.data)})
  const {data:exams}   = useQuery({queryKey:['exams'],  queryFn:()=>apiClient.get('/exams').then(r=>r.data)})
  const [att,  setAtt]  = useState({from_date:'',to_date:'',class_id:''})
  const [fee,  setFee]  = useState({from_date:'',to_date:''})
  const [res,  setRes]  = useState({exam_id:'',class_id:''})

  const download = (endpoint: string, params: Record<string,string>) => {
    const q = new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([,v])=>v)))
    const a = document.createElement('a'); a.href=`/api${endpoint}?${q}`; a.click()
  }

  return (
    <div className="space-y-4">
      <h2 className="text-white font-semibold flex items-center gap-2"><FileSpreadsheet size={16} className="text-green-400"/> Export Reports (Excel)</h2>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">

        {/* Attendance */}
        <div className="bg-gray-900 border border-indigo-500/30 rounded-2xl p-5">
          <div className="text-3xl mb-2">📋</div>
          <h3 className="text-white font-semibold text-sm">Attendance Report</h3>
          <p className="text-gray-400 text-xs mb-4">Student-wise attendance with percentage</p>
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div><label className="block text-gray-500 text-xs mb-1">From</label><input type="date" value={att.from_date} onChange={e=>setAtt({...att,from_date:e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-white text-xs focus:outline-none focus:border-indigo-500"/></div>
              <div><label className="block text-gray-500 text-xs mb-1">To</label><input type="date" value={att.to_date} onChange={e=>setAtt({...att,to_date:e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-white text-xs focus:outline-none focus:border-indigo-500"/></div>
            </div>
            <select value={att.class_id} onChange={e=>setAtt({...att,class_id:e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-gray-300 text-xs focus:outline-none">
              <option value="">All Classes</option>
              {classes?.map((c:any) => <option key={c.id} value={c.id}>{c.name}{c.section?` - ${c.section}`:''}</option>)}
            </select>
            <button onClick={()=>download('/reports/attendance/excel',att)} disabled={!att.from_date||!att.to_date}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-1.5 rounded-lg text-xs font-medium transition">
              <Download size={12}/> Download Excel
            </button>
          </div>
        </div>

        {/* Fees */}
        <div className="bg-gray-900 border border-emerald-500/30 rounded-2xl p-5">
          <div className="text-3xl mb-2">💰</div>
          <h3 className="text-white font-semibold text-sm">Fee Collection Report</h3>
          <p className="text-gray-400 text-xs mb-4">Payments with method and receipt</p>
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div><label className="block text-gray-500 text-xs mb-1">From</label><input type="date" value={fee.from_date} onChange={e=>setFee({...fee,from_date:e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-white text-xs focus:outline-none focus:border-emerald-500"/></div>
              <div><label className="block text-gray-500 text-xs mb-1">To</label><input type="date" value={fee.to_date} onChange={e=>setFee({...fee,to_date:e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-white text-xs focus:outline-none focus:border-emerald-500"/></div>
            </div>
            <button onClick={()=>download('/reports/fees/excel',fee)}
              className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white py-1.5 rounded-lg text-xs font-medium transition">
              <Download size={12}/> Download Excel
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="bg-gray-900 border border-amber-500/30 rounded-2xl p-5">
          <div className="text-3xl mb-2">🏆</div>
          <h3 className="text-white font-semibold text-sm">Exam Results Report</h3>
          <p className="text-gray-400 text-xs mb-4">Class-wise marks with rank list</p>
          <div className="space-y-2">
            <select value={res.exam_id} onChange={e=>setRes({...res,exam_id:e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-gray-300 text-xs focus:outline-none">
              <option value="">Select Exam</option>
              {exams?.map((e:any) => <option key={e.id} value={e.id}>{e.name}</option>)}
            </select>
            <select value={res.class_id} onChange={e=>setRes({...res,class_id:e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-gray-300 text-xs focus:outline-none">
              <option value="">Select Class</option>
              {classes?.map((c:any) => <option key={c.id} value={c.id}>{c.name}{c.section?` - ${c.section}`:''}</option>)}
            </select>
            <button onClick={()=>download('/reports/results/excel',res)} disabled={!res.exam_id||!res.class_id}
              className="w-full flex items-center justify-center gap-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-40 text-white py-1.5 rounded-lg text-xs font-medium transition">
              <Download size={12}/> Download Excel
            </button>
          </div>
        </div>

      </div>
    </div>
  )
}

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div><h1 className="text-white text-xl font-bold">Reports & Analytics</h1><p className="text-gray-400 text-sm">Real-time stats and downloadable Excel reports</p></div>
      <LiveStats/>
      <ExportReports/>
    </div>
  )
}
