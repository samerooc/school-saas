import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { CheckCircle2, XCircle, Clock, ChevronDown, Calendar, Users } from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { format } from 'date-fns'

type Status = 'present' | 'absent' | 'late'

interface AttendanceEntry { student_id: string; status: Status }

async function fetchClasses() {
  const res = await apiClient.get('/classes')
  return res.data
}

async function fetchStudents(classId: string) {
  const res = await apiClient.get(`/students?class_id=${classId}&is_active=true&per_page=100`)
  return res.data.items
}

export default function AttendancePage() {
  const today = format(new Date(), 'yyyy-MM-dd')
  const [selectedClass, setSelectedClass] = useState('')
  const [selectedDate, setSelectedDate] = useState(today)
  const [entries, setEntries] = useState<Record<string, Status>>({})
  const [submitted, setSubmitted] = useState(false)

  const { data: classes } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: students, isLoading: loadingStudents } = useQuery({
    queryKey: ['students-for-attendance', selectedClass],
    queryFn: () => fetchStudents(selectedClass),
    enabled: !!selectedClass,
    onSuccess: (data) => {
      // Default all to present
      const defaults: Record<string, Status> = {}
      data.forEach((s: any) => { defaults[s.id] = 'present' })
      setEntries(defaults)
      setSubmitted(false)
    },
  })

  const submitMutation = useMutation({
    mutationFn: () => apiClient.post('/attendance/bulk', {
      class_id: selectedClass,
      date: selectedDate,
      entries: Object.entries(entries).map(([student_id, status]) => ({ student_id, status })),
    }),
    onSuccess: () => setSubmitted(true),
  })

  const markAll = (status: Status) => {
    if (!students) return
    const all: Record<string, Status> = {}
    students.forEach((s: any) => { all[s.id] = status })
    setEntries(all)
  }

  const toggle = (id: string) => {
    setEntries(prev => ({
      ...prev,
      [id]: prev[id] === 'present' ? 'absent' : prev[id] === 'absent' ? 'late' : 'present',
    }))
  }

  const counts = students ? {
    present: Object.values(entries).filter(s => s === 'present').length,
    absent: Object.values(entries).filter(s => s === 'absent').length,
    late: Object.values(entries).filter(s => s === 'late').length,
  } : null

  if (submitted) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="text-5xl mb-4">✅</div>
          <h2 className="text-white text-xl font-bold">Attendance Submitted!</h2>
          {counts && (
            <div className="flex gap-4 justify-center mt-4 text-sm">
              <span className="text-green-400">Present: {counts.present}</span>
              <span className="text-red-400">Absent: {counts.absent}</span>
              <span className="text-yellow-400">Late: {counts.late}</span>
            </div>
          )}
          <button
            onClick={() => { setSubmitted(false); setSelectedClass('') }}
            className="mt-6 bg-indigo-600 text-white px-6 py-2 rounded-xl hover:bg-indigo-500 transition"
          >
            Mark Another Class
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-white text-xl font-bold">Mark Attendance</h1>
        <p className="text-gray-400 text-sm">Select class and mark each student</p>
      </div>

      {/* Controls */}
      <div className="grid sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-gray-400 text-xs mb-1.5">Select Class</label>
          <div className="relative">
            <select
              value={selectedClass}
              onChange={e => setSelectedClass(e.target.value)}
              className="w-full appearance-none bg-gray-900 border border-gray-700 rounded-xl
                         px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="">Choose a class...</option>
              {classes?.map((c: any) => (
                <option key={c.id} value={c.id}>
                  {c.name}{c.section ? ` - ${c.section}` : ''}
                </option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
          </div>
        </div>
        <div>
          <label className="block text-gray-400 text-xs mb-1.5">Date</label>
          <input
            type="date"
            value={selectedDate}
            max={today}
            onChange={e => setSelectedDate(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5
                       text-white text-sm focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {selectedClass && students && !loadingStudents && (
        <>
          {/* Summary bar */}
          <div className="flex items-center gap-4 bg-gray-900 border border-gray-800 rounded-xl p-3">
            <span className="text-gray-400 text-sm flex items-center gap-1.5">
              <Users size={14} /> {students.length} students
            </span>
            {counts && (
              <>
                <span className="text-green-400 text-sm">✓ {counts.present} Present</span>
                <span className="text-red-400 text-sm">✗ {counts.absent} Absent</span>
                {counts.late > 0 && <span className="text-yellow-400 text-sm">⧗ {counts.late} Late</span>}
              </>
            )}
            <div className="ml-auto flex gap-2">
              <button onClick={() => markAll('present')} className="text-xs text-green-400 hover:text-green-300 transition">
                All Present
              </button>
              <button onClick={() => markAll('absent')} className="text-xs text-red-400 hover:text-red-300 transition">
                All Absent
              </button>
            </div>
          </div>

          {/* Student list */}
          <div className="space-y-2">
            {students.map((student: any, idx: number) => {
              const status = entries[student.id] || 'present'
              return (
                <div
                  key={student.id}
                  onClick={() => toggle(student.id)}
                  className={`flex items-center gap-4 p-3 rounded-xl border cursor-pointer transition
                    ${status === 'present' ? 'bg-green-500/5 border-green-500/20 hover:bg-green-500/10'
                    : status === 'absent' ? 'bg-red-500/5 border-red-500/20 hover:bg-red-500/10'
                    : 'bg-yellow-500/5 border-yellow-500/20 hover:bg-yellow-500/10'}`}
                >
                  <span className="text-gray-500 text-xs w-6 text-right shrink-0">{idx + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{student.full_name}</p>
                    {student.roll_number && (
                      <p className="text-gray-500 text-xs">Roll: {student.roll_number}</p>
                    )}
                  </div>
                  <div className="shrink-0">
                    {status === 'present' ? (
                      <CheckCircle2 size={20} className="text-green-400" />
                    ) : status === 'absent' ? (
                      <XCircle size={20} className="text-red-400" />
                    ) : (
                      <Clock size={20} className="text-yellow-400" />
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Submit */}
          <button
            onClick={() => submitMutation.mutate()}
            disabled={submitMutation.isPending || students.length === 0}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60
                       text-white font-semibold py-3 rounded-xl transition text-sm"
          >
            {submitMutation.isPending
              ? 'Submitting...'
              : `Submit Attendance for ${selectedDate}`}
          </button>

          {submitMutation.isError && (
            <p className="text-red-400 text-sm text-center">
              {(submitMutation.error as any)?.response?.data?.detail || 'Failed to submit'}
            </p>
          )}
        </>
      )}

      {selectedClass && loadingStudents && (
        <div className="flex items-center justify-center h-32">
          <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!selectedClass && (
        <div className="flex items-center justify-center h-40 text-gray-600">
          <div className="text-center">
            <Calendar size={32} className="mx-auto mb-2 opacity-40" />
            <p className="text-sm">Select a class to start marking attendance</p>
          </div>
        </div>
      )}
    </div>
  )
}
