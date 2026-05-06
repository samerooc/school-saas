import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Trophy, ChevronDown, BookOpen } from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { useAuthStore } from '@/stores/authStore'

export default function StudentResultsPage() {
  const user = useAuthStore(s => s.user)
  const [examId, setExamId] = useState('')
  const [studentId, setStudentId] = useState('')

  const { data: exams } = useQuery({
    queryKey: ['exams'],
    queryFn: () => apiClient.get('/exams').then(r => r.data),
  })

  // Auto-fetch student id for student role
  const { data: myStudent } = useQuery({
    queryKey: ['my-student'],
    queryFn: async () => {
      if (user?.role !== 'student') return null
      const me = await apiClient.get('/auth/me').then(r => r.data)
      const students = await apiClient.get('/students?per_page=1').then(r => r.data)
      return students.items?.[0] || null
    },
    onSuccess: (data) => { if (data?.id) setStudentId(data.id) },
  })

  const { data: results, isLoading } = useQuery({
    queryKey: ['results', examId, studentId],
    queryFn: () => apiClient.get(`/exams/${examId}/results/${studentId}`).then(r => r.data),
    enabled: !!(examId && studentId),
    retry: false,
  })

  const gradeColor = (g: string) => {
    if (!g || g === 'F') return 'text-red-400'
    if (g.startsWith('A')) return 'text-green-400'
    if (g.startsWith('B')) return 'text-blue-400'
    return 'text-yellow-400'
  }

  const pctColor = (p: number) => p >= 60 ? 'bg-green-500' : p >= 40 ? 'bg-yellow-500' : 'bg-red-500'

  const downloadMarksheet = () => {
    if (!examId || !studentId) return
    window.open(`/api/exams/${examId}/marksheet/${studentId}/pdf`, '_blank')
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-white text-xl font-bold">Results</h1>
          <p className="text-gray-400 text-sm">View and download marksheet</p>
        </div>
        {results && (
          <button onClick={downloadMarksheet}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition">
            <Download size={14} /> Download PDF
          </button>
        )}
      </div>

      {/* Exam select */}
      <div className="max-w-xs">
        <label className="block text-gray-400 text-xs mb-1.5">Select Exam</label>
        <div className="relative">
          <select value={examId} onChange={e => setExamId(e.target.value)}
            className="w-full appearance-none bg-gray-900 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500">
            <option value="">Choose exam...</option>
            {exams?.filter((e: any) => user?.role === 'student' ? e.is_published : true).map((e: any) => (
              <option key={e.id} value={e.id}>{e.name}</option>
            ))}
          </select>
          <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center h-32 items-center">
          <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {results && (
        <div className="space-y-4">
          {/* Summary card */}
          <div className={`rounded-2xl p-5 border ${results.result === 'PASS' ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-bold text-lg">{results.exam_name}</p>
                <div className="flex items-center gap-4 mt-2 text-sm">
                  <span className="text-gray-300">Total: <b className="text-white">{results.total_obtained}/{results.total_max}</b></span>
                  <span className="text-gray-300">Percentage: <b className={gradeColor(results.overall_grade)}>{results.overall_percentage}%</b></span>
                  <span className="text-gray-300">Grade: <b className={`${gradeColor(results.overall_grade)} text-base`}>{results.overall_grade}</b></span>
                </div>
              </div>
              <div className={`text-2xl font-black ${results.result === 'PASS' ? 'text-green-400' : 'text-red-400'}`}>
                {results.result}
              </div>
            </div>
          </div>

          {/* Subject-wise table */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
            <div className="p-4 border-b border-gray-800">
              <p className="text-white font-semibold text-sm flex items-center gap-2"><BookOpen size={15} />Subject-wise Marks</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left text-gray-400 font-medium px-4 py-3">Subject</th>
                    <th className="text-center text-gray-400 font-medium px-4 py-3">Marks</th>
                    <th className="text-center text-gray-400 font-medium px-4 py-3">Grade</th>
                    <th className="text-left text-gray-400 font-medium px-4 py-3 hidden sm:table-cell">Progress</th>
                  </tr>
                </thead>
                <tbody>
                  {results.subjects.map((s: any) => (
                    <tr key={s.subject_name} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                      <td className="px-4 py-3 text-white">{s.subject_name}</td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-white font-medium">{s.marks_obtained}</span>
                        <span className="text-gray-500">/{s.max_marks}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`font-bold ${gradeColor(s.grade)}`}>{s.grade}</span>
                      </td>
                      <td className="px-4 py-3 hidden sm:table-cell">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-700 rounded-full h-1.5">
                            <div className={`h-1.5 rounded-full ${pctColor(s.percentage)}`}
                              style={{ width: `${Math.min(100, s.percentage)}%` }} />
                          </div>
                          <span className="text-gray-400 text-xs w-10 text-right">{s.percentage}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Download button bottom */}
          <button onClick={downloadMarksheet}
            className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700
                       text-white py-3 rounded-xl transition text-sm border border-gray-700">
            <Download size={15} /> Download Marksheet PDF
          </button>
        </div>
      )}

      {!examId && (
        <div className="flex items-center justify-center h-40 text-gray-600">
          <div className="text-center"><Trophy size={32} className="mx-auto mb-2 opacity-30" /><p className="text-sm">Select an exam to view results</p></div>
        </div>
      )}
    </div>
  )
}
