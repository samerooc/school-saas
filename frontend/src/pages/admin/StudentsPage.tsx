import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Plus, Star, UserCheck, UserX, ChevronLeft, ChevronRight, Filter } from 'lucide-react'
import { apiClient } from '@/services/apiClient'

interface Student {
  id: string
  admission_number: string
  full_name: string
  class_name: string | null
  section: string | null
  roll_number: string | null
  is_active: boolean
  is_premium: boolean
  photo_url: string | null
}

interface PaginatedStudents {
  items: Student[]
  total: number
  page: number
  pages: number
}

async function fetchStudents(params: Record<string, any>): Promise<PaginatedStudents> {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ''))
  )
  const res = await apiClient.get(`/students?${q}`)
  return res.data
}

export default function StudentsPage() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined)
  const [showAddModal, setShowAddModal] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['students', page, search, filterActive],
    queryFn: () => fetchStudents({ page, per_page: 20, search: search || undefined, is_active: filterActive }),
    placeholderData: (prev) => prev,
  })

  const premiumMutation = useMutation({
    mutationFn: ({ id, grant }: { id: string; grant: boolean }) =>
      grant
        ? apiClient.post(`/students/${id}/premium`, null, { params: { expires_in_days: 365 } })
        : apiClient.delete(`/students/${id}/premium`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['students'] }),
  })

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-white text-xl font-bold">Students</h1>
          <p className="text-gray-400 text-sm">{data?.total ?? 0} total students</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white
                     px-4 py-2 rounded-xl text-sm font-medium transition"
        >
          <Plus size={16} /> Add Student
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search name, admission no..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="w-full bg-gray-900 border border-gray-700 rounded-xl pl-9 pr-4 py-2.5
                       text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <select
          value={filterActive === undefined ? '' : String(filterActive)}
          onChange={(e) => {
            setFilterActive(e.target.value === '' ? undefined : e.target.value === 'true')
            setPage(1)
          }}
          className="bg-gray-900 border border-gray-700 rounded-xl px-3 py-2.5 text-gray-300
                     text-sm focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Students</option>
          <option value="true">Active Only</option>
          <option value="false">Inactive Only</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left text-gray-400 font-medium px-4 py-3">Student</th>
                  <th className="text-left text-gray-400 font-medium px-4 py-3 hidden sm:table-cell">Adm. No</th>
                  <th className="text-left text-gray-400 font-medium px-4 py-3 hidden md:table-cell">Class</th>
                  <th className="text-left text-gray-400 font-medium px-4 py-3">Status</th>
                  <th className="text-left text-gray-400 font-medium px-4 py-3">Premium</th>
                  <th className="text-right text-gray-400 font-medium px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((student) => (
                  <tr key={student.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-indigo-600/30 rounded-full flex items-center justify-center
                                        text-indigo-400 text-xs font-bold shrink-0">
                          {student.full_name.charAt(0)}
                        </div>
                        <span className="text-white font-medium">{student.full_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-400 hidden sm:table-cell">
                      {student.admission_number}
                    </td>
                    <td className="px-4 py-3 text-gray-400 hidden md:table-cell">
                      {student.class_name ? `${student.class_name}${student.section ? ` - ${student.section}` : ''}` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium
                        ${student.is_active ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                        {student.is_active ? <UserCheck size={11} /> : <UserX size={11} />}
                        {student.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => premiumMutation.mutate({ id: student.id, grant: !student.is_premium })}
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium
                          transition cursor-pointer
                          ${student.is_premium
                            ? 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30'
                            : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                          }`}
                      >
                        <Star size={10} fill={student.is_premium ? 'currentColor' : 'none'} />
                        {student.is_premium ? 'Premium' : 'Free'}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <a
                        href={`/admin/students/${student.id}`}
                        className="text-indigo-400 hover:text-indigo-300 text-xs transition"
                      >
                        View →
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {data?.items.length === 0 && (
              <div className="text-center py-12 text-gray-500">No students found</div>
            )}
          </div>
        )}
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-gray-400 text-sm">
            Page {data.page} of {data.pages} ({data.total} students)
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-xl bg-gray-900 border border-gray-700 text-gray-400
                         hover:border-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page === data.pages}
              className="p-2 rounded-xl bg-gray-900 border border-gray-700 text-gray-400
                         hover:border-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Add Student Modal */}
      {showAddModal && <AddStudentModal onClose={() => setShowAddModal(false)} onSuccess={() => {
        setShowAddModal(false)
        qc.invalidateQueries({ queryKey: ['students'] })
      }} />}
    </div>
  )
}


// ── Add Student Modal ─────────────────────────────────────────────────────────
function AddStudentModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const { data: classes } = useQuery({
    queryKey: ['classes'],
    queryFn: () => apiClient.get('/classes').then(r => r.data),
  })

  const [form, setForm] = useState({
    full_name: '', email: '', phone: '', class_id: '',
    roll_number: '', gender: '', date_of_birth: '',
    parent_name: '', parent_email: '', parent_phone: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleSubmit = async () => {
    if (!form.full_name || !form.class_id) {
      setError('Name and Class are required')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await apiClient.post('/students', {
        ...form,
        date_of_birth: form.date_of_birth || undefined,
        email: form.email || undefined,
        parent_email: form.parent_email || undefined,
      })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to add student')
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <Modal onClose={onSuccess}>
        <div className="text-center p-4">
          <div className="text-4xl mb-3">🎉</div>
          <h3 className="text-white font-bold text-lg">Student Added!</h3>
          <p className="text-gray-400 text-sm mt-2">Admission Number:</p>
          <p className="text-indigo-400 font-mono font-bold text-lg">{result.admission_number}</p>
          <p className="text-gray-400 text-sm mt-3">Temporary Password:</p>
          <p className="text-yellow-400 font-mono font-bold text-lg">{result.temp_password}</p>
          <p className="text-gray-500 text-xs mt-2">Give this password to the student. They must change it on first login.</p>
          <button onClick={onSuccess} className="mt-5 bg-indigo-600 text-white px-6 py-2 rounded-xl hover:bg-indigo-500 transition">
            Done
          </button>
        </div>
      </Modal>
    )
  }

  return (
    <Modal onClose={onClose}>
      <h3 className="text-white font-bold text-lg mb-5">Add New Student</h3>

      {error && <p className="text-red-400 text-sm bg-red-500/10 rounded-xl p-3 mb-4">{error}</p>}

      <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
        <Section title="Student Details">
          <Row>
            <Field label="Full Name *" value={form.full_name} onChange={v => setForm({ ...form, full_name: v })} />
            <Field label="Email" value={form.email} onChange={v => setForm({ ...form, email: v })} />
          </Row>
          <Row>
            <Field label="Phone" value={form.phone} onChange={v => setForm({ ...form, phone: v })} />
            <div>
              <label className="block text-gray-400 text-xs mb-1">Class *</label>
              <select
                value={form.class_id}
                onChange={e => setForm({ ...form, class_id: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm
                           focus:outline-none focus:border-indigo-500"
              >
                <option value="">Select Class</option>
                {classes?.map((c: any) => (
                  <option key={c.id} value={c.id}>
                    {c.name}{c.section ? ` - ${c.section}` : ''}
                  </option>
                ))}
              </select>
            </div>
          </Row>
          <Row>
            <Field label="Roll Number" value={form.roll_number} onChange={v => setForm({ ...form, roll_number: v })} />
            <Field label="Date of Birth" type="date" value={form.date_of_birth} onChange={v => setForm({ ...form, date_of_birth: v })} />
          </Row>
          <div>
            <label className="block text-gray-400 text-xs mb-1">Gender</label>
            <select
              value={form.gender}
              onChange={e => setForm({ ...form, gender: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm
                         focus:outline-none focus:border-indigo-500"
            >
              <option value="">Select Gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
        </Section>

        <Section title="Parent Details">
          <Row>
            <Field label="Parent Name" value={form.parent_name} onChange={v => setForm({ ...form, parent_name: v })} />
            <Field label="Parent Email" value={form.parent_email} onChange={v => setForm({ ...form, parent_email: v })} />
          </Row>
          <Field label="Parent Phone" value={form.parent_phone} onChange={v => setForm({ ...form, parent_phone: v })} />
        </Section>
      </div>

      <div className="flex gap-3 mt-5">
        <button onClick={onClose} className="flex-1 bg-gray-800 text-gray-300 py-2.5 rounded-xl hover:bg-gray-700 transition text-sm">
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="flex-1 bg-indigo-600 text-white py-2.5 rounded-xl hover:bg-indigo-500 disabled:opacity-60 transition text-sm font-medium"
        >
          {loading ? 'Adding...' : 'Add Student'}
        </button>
      </div>
    </Modal>
  )
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-lg"
           onClick={e => e.stopPropagation()}>
        {children}
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-3">{title}</p>
      <div className="space-y-3">{children}</div>
    </div>
  )
}

function Row({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-2 gap-3">{children}</div>
}

function Field({ label, value, onChange, type = 'text' }: {
  label: string; value: string; onChange: (v: string) => void; type?: string
}) {
  return (
    <div>
      <label className="block text-gray-400 text-xs mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm
                   focus:outline-none focus:border-indigo-500 placeholder-gray-600"
      />
    </div>
  )
}
