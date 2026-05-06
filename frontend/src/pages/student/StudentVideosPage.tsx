import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Youtube, Tv2, Star, Lock, Play, FileText, BookOpen } from 'lucide-react'
import { apiClient } from '@/services/apiClient'

function SecureVideoPlayer({ videoId }: { videoId: string }) {
  const { data: token, isLoading, error } = useQuery({
    queryKey: ['video-token', videoId],
    queryFn: () => apiClient.get(`/videos/${videoId}/player-token`).then(r => r.data),
    staleTime: 50 * 60 * 1000, retry: false,
  })
  if (isLoading) return <div className="w-full aspect-video bg-gray-900 rounded-2xl flex items-center justify-center"><div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>
  if (error) {
    const s = (error as any)?.response?.status
    return (
      <div className="w-full aspect-video bg-gray-900 rounded-2xl flex items-center justify-center border border-gray-800">
        <div className="text-center px-4">
          {s === 402 ? <><Star size={32} className="text-yellow-400 mx-auto mb-2" /><p className="text-white font-semibold">Premium Content</p><p className="text-gray-400 text-sm mt-1">Contact admin to unlock</p></>
           : s === 403 ? <><Lock size={32} className="text-red-400 mx-auto mb-2" /><p className="text-white font-semibold">Access Denied</p><p className="text-gray-400 text-sm mt-1">Not for your class</p></>
           : <p className="text-red-400">Failed to load video</p>}
        </div>
      </div>
    )
  }
  const embedUrl = token?.youtube?.embed_url || token?.cloudflare?.signed_url
  if (!embedUrl) return null
  return (
    <div className="w-full aspect-video rounded-2xl overflow-hidden bg-black">
      <iframe src={embedUrl} className="w-full h-full" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen title={token?.title} />
    </div>
  )
}

export default function StudentVideosPage() {
  const [selectedVideo, setSelectedVideo] = useState<any>(null)
  const [activeChapter, setActiveChapter] = useState<string | null>(null)
  const { data: videosData, isLoading } = useQuery({ queryKey: ['student-videos'], queryFn: () => apiClient.get('/videos').then(r => r.data) })
  const { data: attachments } = useQuery({ queryKey: ['attachments', selectedVideo?.id], queryFn: () => apiClient.get(`/videos/${selectedVideo.id}/attachments`).then(r => r.data), enabled: !!selectedVideo?.id })
  const videos = videosData?.items || []
  const chapters: Record<string, any[]> = {}
  videos.forEach((v: any) => { const ch = v.chapter_name || 'Other'; if (!chapters[ch]) chapters[ch] = []; chapters[ch].push(v) })
  const chapterNames = Object.keys(chapters)
  const currentChapter = activeChapter || chapterNames[0] || null
  const chapterVideos = currentChapter ? (chapters[currentChapter] || []) : []
  const getYtId = (v: any) => { const t = v.thumbnail_url; if (t?.includes('img.youtube.com')) return t.split('/vi/')[1]?.split('/')[0]; return null }

  return (
    <div className="space-y-5">
      <div><h1 className="text-white text-xl font-bold">My Videos</h1><p className="text-gray-400 text-sm">Study materials from your teachers</p></div>
      {isLoading ? <div className="flex justify-center h-48 items-center"><div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div> : (
        <div className="grid lg:grid-cols-3 gap-5">
          <div className="lg:col-span-1 space-y-3">
            {chapterNames.length > 1 && (
              <div className="flex flex-wrap gap-2">
                {chapterNames.map(ch => <button key={ch} onClick={() => { setActiveChapter(ch); setSelectedVideo(null) }} className={`text-xs px-3 py-1.5 rounded-xl transition ${currentChapter === ch ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}>{ch}</button>)}
              </div>
            )}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
              <div className="p-3 border-b border-gray-800"><p className="text-gray-400 text-xs font-medium uppercase tracking-wider">{currentChapter || 'Videos'} · {chapterVideos.length}</p></div>
              <div className="divide-y divide-gray-800/50 max-h-[60vh] overflow-y-auto">
                {chapterVideos.map((v: any) => (
                  <div key={v.id} onClick={() => setSelectedVideo(v)} className={`flex gap-3 p-3 cursor-pointer transition border-l-2 ${selectedVideo?.id === v.id ? 'bg-indigo-600/10 border-indigo-500' : 'border-transparent hover:bg-gray-800'}`}>
                    <div className="w-20 shrink-0 aspect-video bg-gray-800 rounded-lg overflow-hidden">
                      {getYtId(v) ? <img src={`https://img.youtube.com/vi/${getYtId(v)}/default.jpg`} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Play size={12} className="text-gray-600" /></div>}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-xs font-medium leading-tight line-clamp-2">{v.title}</p>
                      {v.topic_name && <p className="text-gray-500 text-xs mt-0.5">{v.topic_name}</p>}
                      <div className="flex gap-1 mt-1">
                        {v.is_premium && <Star size={9} className="text-yellow-400" />}
                        {v.has_youtube && <Youtube size={9} className="text-red-400" />}
                      </div>
                    </div>
                  </div>
                ))}
                {chapterVideos.length === 0 && <div className="p-6 text-center text-gray-600 text-sm">No videos</div>}
              </div>
            </div>
          </div>
          <div className="lg:col-span-2 space-y-4">
            {selectedVideo ? (
              <>
                <SecureVideoPlayer videoId={selectedVideo.id} />
                <div>
                  <h2 className="text-white font-bold">{selectedVideo.title}</h2>
                  <p className="text-gray-400 text-sm">{selectedVideo.chapter_name}{selectedVideo.topic_name ? ` · ${selectedVideo.topic_name}` : ''}</p>
                </div>
                <div className="bg-gray-900 border border-gray-800 rounded-2xl">
                  <div className="p-3 border-b border-gray-800"><p className="text-gray-400 text-xs font-medium flex items-center gap-1"><FileText size={11} /> Notes & PDFs</p></div>
                  <div className="p-4">
                    {attachments?.length > 0 ? (
                      <div className="space-y-2">
                        {attachments.map((att: any) => (
                          <a key={att.id} href={`/api/videos/${selectedVideo.id}/attachments/${att.id}/download`} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-3 p-3 bg-gray-800 rounded-xl hover:bg-gray-700 transition">
                            <div className="w-8 h-8 bg-red-500/10 rounded-lg flex items-center justify-center"><FileText size={13} className="text-red-400" /></div>
                            <div className="flex-1 min-w-0"><p className="text-white text-sm truncate">{att.title}</p><p className="text-gray-500 text-xs">{att.file_size_kb} KB</p></div>
                            <span className="text-indigo-400 text-xs">↓</span>
                          </a>
                        ))}
                      </div>
                    ) : <div className="text-center py-4 text-gray-600 text-sm"><BookOpen size={20} className="mx-auto mb-1 opacity-40" />No notes attached</div>}
                  </div>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-600">
                <div className="text-center"><Play size={40} className="mx-auto mb-3 opacity-30" /><p className="text-sm">Select a video to watch</p></div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
