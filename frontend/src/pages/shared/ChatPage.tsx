import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, MessageCircle, Circle } from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { useAuthStore } from '@/stores/authStore'

interface Message { id:string; sender_id:string; receiver_id:string; text:string; read:boolean; created_at:string }
interface Conversation { partner_id:string; partner_name:string; partner_role:string; last_message:string|null; unread_count:number; is_online:boolean }

export default function ChatPage() {
  const user = useAuthStore(s => s.user)
  const qc   = useQueryClient()
  const [selected, setSelected] = useState<Conversation|null>(null)
  const [text, setText]         = useState('')
  const [msgs, setMsgs]         = useState<Message[]>([])
  const endRef = useRef<HTMLDivElement>(null)

  const {data:conversations=[]} = useQuery<Conversation[]>({
    queryKey:['conversations'],
    queryFn:()=>apiClient.get('/chat/conversations').then(r=>r.data),
    refetchInterval:30000,
  })

  useQuery({
    queryKey:['messages',selected?.partner_id],
    queryFn:()=>apiClient.get(`/chat/messages/${selected?.partner_id}`).then(r=>r.data),
    enabled:!!selected,
    onSuccess:(data:any)=>setMsgs(data.messages||[]),
  })

  const sendMut = useMutation({
    mutationFn:(t:string)=>apiClient.post(`/chat/messages/${selected?.partner_id}?text=${encodeURIComponent(t)}`),
    onSuccess:()=>qc.invalidateQueries({queryKey:['conversations']}),
  })

  useEffect(()=>{ endRef.current?.scrollIntoView({behavior:'smooth'}) },[msgs])

  const handleSend = () => {
    if(!text.trim()||!selected) return
    const t=text.trim(); setText('')
    sendMut.mutate(t)
    setMsgs(prev=>[...prev,{id:`tmp-${Date.now()}`,sender_id:user?.id||'',receiver_id:selected.partner_id,text:t,read:false,created_at:new Date().toISOString()}])
  }

  const rc=(r:string)=>r==='teacher'?'text-violet-400':r==='parent'?'text-emerald-400':'text-indigo-400'
  const myMsgs = selected ? msgs.filter(m=>(m.sender_id===user?.id&&m.receiver_id===selected.partner_id)||(m.sender_id===selected.partner_id&&m.receiver_id===user?.id)) : []

  return (
    <div className="h-[calc(100vh-120px)] flex bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
      {/* Conversation list */}
      <div className={`w-full sm:w-72 shrink-0 border-r border-gray-800 flex flex-col ${selected?'hidden sm:flex':'flex'}`}>
        <div className="p-4 border-b border-gray-800"><h2 className="text-white font-bold text-sm flex items-center gap-2"><MessageCircle size={15} className="text-indigo-400"/> Messages</h2></div>
        <div className="flex-1 overflow-y-auto">
          {(conversations as Conversation[]).length===0 ? (
            <div className="p-6 text-center text-gray-600"><MessageCircle size={24} className="mx-auto mb-2 opacity-40"/><p className="text-xs">No conversations yet</p></div>
          ) : (conversations as Conversation[]).map(conv=>(
            <button key={conv.partner_id} onClick={()=>setSelected(conv)}
              className={`w-full flex items-center gap-3 p-4 border-b border-gray-800/50 hover:bg-gray-800/50 transition text-left ${selected?.partner_id===conv.partner_id?'bg-indigo-600/10 border-l-2 border-l-indigo-500':''}`}>
              <div className="relative shrink-0">
                <div className="w-9 h-9 bg-gray-700 rounded-full flex items-center justify-center text-white text-sm font-bold">{conv.partner_name.charAt(0)}</div>
                {conv.is_online && <Circle size={8} className="absolute bottom-0 right-0 text-green-400 fill-green-400"/>}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-white text-sm font-medium truncate">{conv.partner_name}</p>
                  {conv.unread_count>0 && <span className="bg-indigo-600 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center shrink-0">{conv.unread_count}</span>}
                </div>
                <p className={`text-xs capitalize ${rc(conv.partner_role)}`}>{conv.partner_role}</p>
                {conv.last_message && <p className="text-gray-500 text-xs truncate mt-0.5">{conv.last_message}</p>}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Chat window */}
      {selected ? (
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center gap-3 p-4 border-b border-gray-800">
            <button onClick={()=>setSelected(null)} className="text-gray-400 sm:hidden">←</button>
            <div className="relative">
              <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-white text-sm font-bold">{selected.partner_name.charAt(0)}</div>
              {selected.is_online && <Circle size={8} className="absolute bottom-0 right-0 text-green-400 fill-green-400"/>}
            </div>
            <div><p className="text-white text-sm font-medium">{selected.partner_name}</p><p className={`text-xs capitalize ${rc(selected.partner_role)}`}>{selected.is_online?'🟢 Online':selected.partner_role}</p></div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {myMsgs.map(msg=>{
              const isMe=msg.sender_id===user?.id
              return (
                <div key={msg.id} className={`flex ${isMe?'justify-end':'justify-start'}`}>
                  <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${isMe?'bg-indigo-600 text-white rounded-br-sm':'bg-gray-800 text-gray-200 rounded-bl-sm'}`}>
                    <p className="leading-relaxed">{msg.text}</p>
                    <p className={`text-xs mt-1 ${isMe?'text-indigo-200':'text-gray-500'}`}>{new Date(msg.created_at).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'})}</p>
                  </div>
                </div>
              )
            })}
            {myMsgs.length===0 && <div className="flex items-center justify-center h-32 text-gray-600"><p className="text-sm">Start the conversation!</p></div>}
            <div ref={endRef}/>
          </div>
          <div className="p-4 border-t border-gray-800 flex items-center gap-3">
            <input type="text" value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=>e.key==='Enter'&&!e.shiftKey&&handleSend()} maxLength={1000}
              placeholder="Type a message..." className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-500"/>
            <button onClick={handleSend} disabled={!text.trim()} className="w-10 h-10 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-xl flex items-center justify-center transition shrink-0"><Send size={16} className="text-white"/></button>
          </div>
        </div>
      ) : (
        <div className="hidden sm:flex flex-1 items-center justify-center text-gray-600">
          <div className="text-center"><MessageCircle size={40} className="mx-auto mb-3 opacity-30"/><p className="text-sm">Select a conversation</p></div>
        </div>
      )}
    </div>
  )
}
