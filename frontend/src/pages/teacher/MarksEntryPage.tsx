import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Save, CheckCircle, ChevronDown } from 'lucide-react'
import { apiClient } from '@/services/apiClient'

export default function MarksEntryPage() {
  const [examId, setExamId] = useState('')
  const [classId, setClassId] = useState('')
  const [subjectId, setSubjectId] = useState('')
  const [marks, setMarks] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState(false)

  const { data: exams } = useQuery({ queryKey: ['exams'], queryFn: () => apiClient.get('/exams').then(r => r.data) })
  const { data: classes } = useQuery({ queryKey: ['classes'], queryFn: () => apiClient.get('/classes').then(r => r.data) })
  const { data: subjects } = useQuery({
    queryKey: ['subjects', classId],
    queryFn: () => apiClient.get(`/classes/${classId}/subjects`).then(r => r.data),
    enabled: !!classId,
  })
  const { data: students, isLoading: loadingStudents } = useQuery({
    queryKey: ['marks-entry', examId, classId, subjectId],
    queryFn: () => apiClient.get(`/exams/${examId}/marks/class/${classId}?subject_id=${subjectId}`).then(r => r.data),
    enabled: !!(examId && classId && subjectId),
    onSuccess: (data) => {
      const m: Record<string, string> = {}
      data.forEach((s: any) => { m[s.student_id] = s.marks_obtained !== null ? String(s.marks_obtained) : '' })
      setMarks(m)
    },
  })

  const saveMutation = useMutation({
    mutationFn: () => apiClient.post(`/exams/${examId}/marks`, 
      Object.entries(marks)
        .filter(([, v]) => v !== '')
        .map(([student_id, marks_obtained]) => ({ student_id, subject_id: subjectId, marks_obtained: parseFloat(marks_obtained) }))
    ),
    onSuccess: () => { setSaved(true); setTimeout(() => setSaved(false), 3000) },
  })

  const maxMarks = subjects?.find((s: any) => s.id === subjectId)?.max_marks || 100

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-white text-xl font-bold">Marks Entry</h1>
        <p className="text-gray-400 text-sm">Select exam, class and subject to enter marks</p>
      </div>

      {/* Filters */}
      <div className="grid sm:grid-cols-3 gap-3">
        {[
          { label: 'Exam', value: examId, onChange: setExamId, options: exams?.map((e: any) => ({ id: e.id, label: e.name })) },
          { label: 'Class', value: classId, onChange: (v: string) => { setClassId(v); setSubjectId('') }, options: classes?.map((c: any) => ({ id: c.id, label: `${c.name}${c.section ? ` - ${c.section}` : ''}` })) },
          { label: 'Subject', value: subjectId, onChange: setSubjectId, options: subjects?.map((s: any) => ({ id: s.id, label: s.name })) },
        ].map(({ label, value, onChange, options }) => (
          <div key={label}>
            <label className="block text-gray-400 text-xs mb-1.5">{label}</label>
            <div className="relative">
              <select value={value} onChange={e => onChange(e.target.value)}
                className="w-full appearance-none bg-gray-900 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500">
                <option value="">Select {label}</option>
                {options?.map((o: any) => <option key={o.id} value={o.id}>{o.label}</option>)}
              </select>
              <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
            </div>
          </div>
        ))}
      </div>

      {/* Marks table */}
      {loadingStudents && (
        <div className="flex justify-center h-32 items-center">
          <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {students && students.length > 0 && (
        <>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-800">
              <p className="text-white font-medium text-sm">{students.length} Students · Max Marks: {maxMarks}</p>
              <div className="flex gap-2">
                <button onClick={() => setMarks(Object.fromEntries(students.map((s: any) => [s.student_id, String(maxMarks)])))}
                  className="text-xs text-green-400 hover:text-green-300 transition">Fill Max</button>
                <button onClick={() => setMarks(Object.fromEntries(students.map((s: any) => [s.student_id, '0'])))}
                  className="text-xs text-red-400 hover:text-red-300 transition">Fill 0</button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left text-gray-400 font-medium px-4 py-3">Student</th>
                    <th className="text-left text-gray-400 font-medium px-4 py-3 hidden sm:table-cell">Roll No</th>
                    <th className="text-left text-gray-400 font-medium px-4 py-3">Marks / {maxMarks}</th>
                    <th className="text-left text-gray-400 font-medium px-4 py-3">Grade</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s: any) => {
                    const val = marks[s.student_id] || ''
                    const num = parseFloat(val)
                    const pct = !isNaN(num) ? (num / maxMarks * 100) : 0
                    const grade = !isNaN(num) ? (pct >= 90 ? 'A+' : pct >= 80 ? 'A' : pct >= 70 ? 'B+' : pct >= 60 ? 'B' : pct >= 50 ? 'C' : pct >= 40 ? 'D' : 'F') : '—'
                    const gradeColor = grade === 'F' ? 'text-red-400' : grade.startsWith('A') ? 'text-green-400' : grade.startsWith('B') ? 'text-blue-400' : 'text-yellow-400'
                    return (
                      <tr key={s.student_id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                        <td className="px-4 py-2.5">
                          <p className="text-white text-sm">{s.student_name}</p>
                        </td>
                        <td className="px-4 py-2.5 text-gray-400 hidden sm:table-cell text-xs">{s.roll_number || '—'}</td>
                        <td className="px-4 py-2.5">
                          <input
                            type="number" min="0" max={maxMarks} step="0.5"
                            value={val}
                            onChange={e => setMarks(prev => ({ ...prev, [s.student_id]: e.target.value }))}
                            className="w-20 bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-white text-sm
                                       focus:outline-none focus:border-indigo-500 text-center"
                            placeholder="—"
                          />
                        </td>
                        <td className="px-4 py-2.5">
                          <span className={`font-bold text-sm ${gradeColor}`}>{grade}</span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500
                       disabled:opacity-60 text-white font-semibold py-3 rounded-xl transition text-sm"
          >
            {saved ? (
              <><CheckCircle size={16} className="text-green-400" /> Marks Saved!</>
            ) : saveMutation.isPending ? (
              'Saving...'
            ) : (
              <><Save size={16} /> Save Marks</>
            )}
          </button>

          {saveMutation.isError && (
            <p className="text-red-400 text-sm text-center">
              {(saveMutation.error as any)?.response?.data?.detail || 'Failed to save marks'}
            </p>
          )}
        </>
      )}

      {examId && classId && subjectId && !loadingStudents && (!students || students.length === 0) && (
        <div className="text-center py-12 text-gray-600">No students found for this class</div>
      )}
    </div>
  )
}
