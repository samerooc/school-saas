import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Video, Radio, Eye, EyeOff, Trash2, ExternalLink, CheckCircle, Link } from 'lucide-react'
import { apiClient } from '@/services/apiClient'

function G({ label, children }: { label: string; children: React.ReactNode }) {
  return <div><label className="block text-gray-400 text-xs mb-1">{label}</label>{children}</div>
}

function Modal({ children, onClose }: any) {
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg p-6" onClick={(e: any) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  )
}

function AddVideoModal({ classes, onClose, onSuccess }: any) {
  const [form, setForm] = useState({ title: '', yt_url: '', class_id: '', chapter_name: '', topic_name: '', description: '', is_premium: false })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)

  const handleUrl = (url: string) => {
    setForm(f => ({ ...f, yt_url: url }))
    const m = url.match(/(?:youtu\.be\/|watch\?v=|embed\/|live\/)([a-zA-Z0-9_-]{11})/)
    setPreview(m ? `https://img.youtube.com/vi/${m[1]}/mqdefault.jpg` : null)
  }

  const submit = async () => {
    if (!form.title || !form.yt_url || !form.class_id) { setError('Title, YouTube URL, and Class required'); return }
    setLoading(true); setError('')
    try { await apiClient.post('/videos', form); onSuccess() }
    catch (e: any) { setError(e?.response?.data?.detail || 'Failed') }
    finally { setLoading(false) }
  }

  return (
    <Modal onClose={onClose}>
      <h3 className="text-white font-bold text-lg mb-5 flex items-center gap-2"><Link size={18} className="text-indigo-400" />Add Video</h3>
      {error && <p className="text-red-400 text-sm bg-red-500/10 rounded-xl p-3 mb-4">{error}</p>}
      <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
        <G label="YouTube URL * (unlisted link paste karo)">
          <input type="url" value={form.yt_url} onChange={e => handleUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 font-mono" />
        </G>
        {preview && (
          <div className="relative rounded-xl overflow-hidden">
            <img src={preview} alt="Preview" className="w-full rounded-xl" />
            <div className="absolute bottom-2 left-2 bg-black/70 text-green-400 text-xs px-2 py-1 rounded-lg flex items-center gap-1">
              <CheckCircle size={10} /> URL valid
            </div>
          </div>
        )}
        <G label="Title *">
          <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="Chapter 5 - Newton's Laws"
            className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500" />
        </G>
        <div className="grid grid-cols-2 gap-3">
          <G label="Class *">
            <select value={form.class_id} onChange={e => setForm(f => ({ ...f, class_id: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500">
              <option value="">Select</option>
              {classes?.map((c: any) => <option key={c.id} value={c.id}>{c.name}{c.section ? ` - ${c.section}` : ''}</option>)}
            </select>
          </G>
          <G label="Chapter">
            <input value={form.chapter_name} onChange={e => setForm(f => ({ ...f, chapter_name: e.target.value }))} placeholder="Chapter 5"
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500" />
          </G>
        </div>
        <G label="Topic">
          <input value={form.topic_name} onChange={e => setForm(f => ({ ...f, topic_name: e.target.value }))} placeholder="Newton's First Law"
            className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500" />
        </G>
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={form.is_premium} onChange={e => setForm(f => ({ ...f, is_premium: e.target.checked }))} className="w-4 h-4 accent-yellow-500" />
          <span className="text-gray-300 text-sm">⭐ Premium content</span>
        </label>
      </div>
      <div className="flex gap-3 mt-5">
        <button onClick={onClose} className="flex-1 bg-gray-800 text-gray-300 py-2.5 rounded-xl text-sm">Cancel</button>
        <button onClick={submit} disabled={loading} className="flex-1 bg-indigo-600 text-white py-2.5 rounded-xl hover:bg-indigo-500 disabled:opacity-60 transition text-sm font-medium">
          {loading ? 'Adding...' : 'Add Video'}
        </button>
      </div>
    </Modal>
  )
}

function LiveModal({ classes, onClose, onSuccess }: any) {
  const [form, setForm] = useState({ title: '', class_id: '', scheduled_at: '', duration_minutes: 60, yt_live_url: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    if (!form.title || !form.class_id || !form.scheduled_at) { setError('Title, Class, Date/Time required'); return }
    setLoading(true)
    try { await apiClient.post('/live', { ...form, scheduled_at: new Date(form.scheduled_at).toISOString() }); onSuccess() }
    catch (e: any) { setError(e?.response?.data?.detail || 'Failed') }
    finally { setLoading(false) }
  }

  return (
    <Modal onClose={onClose}>
      <h3 className="text-white font-bold text-lg mb-5 flex items-center gap-2"><Radio size={18} className="text-red-400" />Schedule Live Class</h3>
      {error && <p className="text-red-400 text-sm bg-red-500/10 rounded-xl p-3 mb-4">{error}</p>}
      <div className="space-y-3">
        <G label="Title *"><input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="Live Doubt Session"
          className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-red-500" /></G>
        <div className="grid grid-cols-2 gap-3">
          <G label="Class *"><select value={form.class_id} onChange={e => setForm(f => ({ ...f, class_id: e.target.value }))}
            className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-red-500">
            <option value="">Select</option>
            {classes?.map((c: any) => <option key={c.id} value={c.id}>{c.name}{c.section ? ` - ${c.section}` : ''}</option>)}
          </select></G>
          <G label="Duration (mins)"><input type="number" value={form.duration_minutes} onChange={e => setForm(f => ({ ...f, duration_minutes: +e.target.value }))}
            className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-red-500" /></G>
        </div>
        <G label="Date & Time *"><input type="datetime-local" value={form.scheduled_at} onChange={e => setForm(f => ({ ...f, scheduled_at: e.target.value }))}
          className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-red-500" /></G>
        <G label="YouTube Live URL (baad mein add kar sakte ho)">
          <input value={form.yt_live_url} onChange={e => setForm(f => ({ ...f, yt_live_url: e.target.value }))} placeholder="https://www.youtube.com/live/..."
            className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-red-500 font-mono" />
          <p className="text-gray-600 text-xs mt-1">YT pe live stream shuru karo → URL copy karo → yahan paste karo</p>
        </G>
      </div>
      <div className="flex gap-3 mt-5">
        <button onClick={onClose} className="flex-1 bg-gray-800 text-gray-300 py-2.5 rounded-xl text-sm">Cancel</button>
        <button onClick={submit} disabled={loading} className="flex-1 bg-red-600 text-white py-2.5 rounded-xl hover:bg-red-500 disabled:opacity-60 transition text-sm font-medium">
          {loading ? 'Scheduling...' : 'Schedule'}
        </button>
      </div>
    </Modal>
  )
}

export default function VideoManagerPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<'videos' | 'live'>('videos')
  const [showAdd, setShowAdd] = useState(false)
  const [showLive, setShowLive] = useState(false)
  const [selectedClass, setSelectedClass] = useState('')

  const { data: classes } = useQuery({ queryKey: ['classes'], queryFn: () => apiClient.get('/classes').then(r => r.data) })
  const { data: videosData, isLoading } = useQuery({
    queryKey: ['videos', selectedClass],
    queryFn: () => apiClient.get(`/videos${selectedClass ? `?class_id=${selectedClass}` : ''}`).then(r => r.data),
  })
  const { data: liveData } = useQuery({
    queryKey: ['live', selectedClass],
    queryFn: () => apiClient.get(`/live${selectedClass ? `?class_id=${selectedClass}` : ''}`).then(r => r.data),
    enabled: tab === 'live',
  })

  const publishMutation = useMutation({
    mutationFn: ({ id, pub }: { id: string; pub: boolean }) => apiClient.patch(`/videos/${id}`, { is_published: pub }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['videos'] }),
  })
  const liveStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => apiClient.patch(`/live/${id}/status?status=${status}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['live'] }),
  })
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/videos/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['videos'] }),
  })

  const done = () => { qc.invalidateQueries({ queryKey: ['videos'] }); setShowAdd(false) }
  const liveDone = () => { qc.invalidateQueries({ queryKey: ['live'] }); setShowLive(false) }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div><h1 className="text-white text-xl font-bold">Video LMS</h1><p className="text-gray-400 text-sm">YT link paste karo, manage karo</p></div>
        <div className="flex gap-2">
          <button onClick={() => setShowAdd(true)} className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition"><Video size={14} />Add Video</button>
          <button onClick={() => setShowLive(true)} className="flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition"><Radio size={14} />Go Live</button>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex bg-gray-900 border border-gray-800 rounded-xl p-1">
          {(['videos', 'live'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-lg text-sm transition font-medium ${tab === t ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'}`}>
              {t === 'live' ? '🔴 Live' : '📹 Videos'}
            </button>
          ))}
        </div>
        <select value={selectedClass} onChange={e => setSelectedClass(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-xl px-3 py-2 text-gray-300 text-sm focus:outline-none">
          <option value="">All Classes</option>
          {classes?.map((c: any) => <option key={c.id} value={c.id}>{c.name}{c.section ? ` - ${c.section}` : ''}</option>)}
        </select>
      </div>

      {tab === 'videos' && (
        <div className="space-y-3">
          {isLoading && <div className="flex justify-center py-12"><div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>}
          {!isLoading && videosData?.items?.length === 0 && (
            <div className="text-center py-16 text-gray-600"><Video size={40} className="mx-auto mb-3 opacity-30" /><p>No videos. Paste a YouTube link!</p></div>
          )}
          {videosData?.items?.map((v: any) => (
            <div key={v.id} className="flex gap-4 bg-gray-900 border border-gray-800 rounded-2xl p-4 hover:border-gray-700 transition">
              <div className="w-28 h-16 rounded-xl overflow-hidden shrink-0 bg-gray-800 relative">
                {v.thumbnail_url && <img src={v.thumbnail_url} alt={v.title} className="w-full h-full object-cover" />}
                {v.is_premium && <div className="absolute top-1 left-1 bg-yellow-500 text-black text-[9px] font-bold px-1 rounded-full">⭐</div>}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-white text-sm font-medium leading-tight">{v.title}</p>
                    {v.chapter_name && <p className="text-gray-500 text-xs mt-0.5">{v.chapter_name}{v.topic_name ? ` › ${v.topic_name}` : ''}</p>}
                    <p className="text-gray-600 text-xs mt-1">👁 {v.view_count}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${v.is_published ? 'bg-green-500/10 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
                    {v.is_published ? 'Published' : 'Draft'}
                  </span>
                </div>
                <div className="flex gap-2 mt-2 flex-wrap">
                  <button onClick={() => publishMutation.mutate({ id: v.id, pub: !v.is_published })}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs transition ${v.is_published ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-green-600 text-white hover:bg-green-500'}`}>
                    {v.is_published ? <><EyeOff size={10} />Unpublish</> : <><Eye size={10} />Publish</>}
                  </button>
                  {v.yt_video_id && (
                    <a href={`https://youtu.be/${v.yt_video_id}`} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs bg-gray-700 text-gray-300 hover:bg-gray-600 transition">
                      <ExternalLink size={10} />YT
                    </a>
                  )}
                  <button onClick={() => { if (confirm('Delete?')) deleteMutation.mutate(v.id) }}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs bg-red-500/10 text-red-400 hover:bg-red-500/20 transition">
                    <Trash2 size={10} />Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'live' && (
        <div className="space-y-3">
          {!liveData?.length && <div className="text-center py-16 text-gray-600"><Radio size={40} className="mx-auto mb-3 opacity-30" /><p>No live classes scheduled</p></div>}
          {liveData?.map((lc: any) => (
            <div key={lc.id} className={`bg-gray-900 border rounded-2xl p-4 ${lc.is_live_now ? 'border-red-500/50 bg-red-500/5' : 'border-gray-800'}`}>
              <div className="flex items-center gap-2 mb-1">
                {lc.is_live_now && <span className="text-xs bg-red-600 text-white px-2 py-0.5 rounded-full font-bold animate-pulse">🔴 LIVE</span>}
                <p className="text-white text-sm font-medium">{lc.title}</p>
              </div>
              <p className="text-gray-400 text-xs">{new Date(lc.scheduled_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })} · {lc.status}</p>
              <div className="flex gap-2 mt-3">
                {lc.status === 'scheduled' && (
                  <button onClick={() => liveStatusMutation.mutate({ id: lc.id, status: 'live' })}
                    className="px-3 py-1.5 rounded-lg text-xs bg-red-600 text-white hover:bg-red-500 transition font-medium">🔴 Go Live</button>
                )}
                {lc.status === 'live' && (
                  <button onClick={() => liveStatusMutation.mutate({ id: lc.id, status: 'ended' })}
                    className="px-3 py-1.5 rounded-lg text-xs bg-gray-700 text-gray-300 hover:bg-gray-600 transition">⏹ End</button>
                )}
                {lc.embed_url && (
                  <a href={lc.embed_url.replace('/embed/', '/watch?v=').split('?')[0]} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-gray-700 text-gray-300 hover:bg-gray-600 transition">
                    <ExternalLink size={10} />Open YT
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {showAdd && <AddVideoModal classes={classes} onClose={() => setShowAdd(false)} onSuccess={done} />}
      {showLive && <LiveModal classes={classes} onClose={() => setShowLive(false)} onSuccess={liveDone} />}
    </div>
  )
}
