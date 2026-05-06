import { useState } from 'react'
import { GraduationCap, Menu, X, Phone, Mail, MapPin, ChevronRight, BookOpen, Users, Trophy, Star, ArrowRight } from 'lucide-react'

function Navbar() {
  const [open, setOpen] = useState(false)
  const links = ['Home','About','Admissions','Courses','Contact']
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-950/90 backdrop-blur border-b border-gray-800">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center"><GraduationCap size={18} className="text-white" /></div>
          <div><p className="text-white font-bold text-sm leading-tight">Springfield Academy</p><p className="text-gray-400 text-xs">Excellence in Education</p></div>
        </div>
        <div className="hidden md:flex items-center gap-6">
          {links.map(l => <a key={l} href={`#${l.toLowerCase()}`} className="text-gray-400 hover:text-white text-sm transition">{l}</a>)}
        </div>
        <a href="/login" className="hidden md:block bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-xl transition font-medium">Student Login</a>
        <button onClick={() => setOpen(!open)} className="text-gray-400 md:hidden">{open ? <X size={22}/> : <Menu size={22}/>}</button>
      </div>
      {open && (
        <div className="md:hidden bg-gray-900 border-t border-gray-800 px-4 py-4 space-y-2">
          {links.map(l => <a key={l} href={`#${l.toLowerCase()}`} onClick={() => setOpen(false)} className="block text-gray-300 text-sm py-1">{l}</a>)}
          <a href="/login" className="block bg-indigo-600 text-white text-sm px-4 py-2 rounded-xl text-center mt-2">Student Login</a>
        </div>
      )}
    </nav>
  )
}

function Hero() {
  return (
    <section id="home" className="relative min-h-screen flex items-center bg-gray-950 pt-16">
      <div className="absolute inset-0 opacity-[0.03]" style={{backgroundImage:'radial-gradient(circle,#fff 1px,transparent 1px)',backgroundSize:'40px 40px'}}/>
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl"/>
      <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-violet-600/20 rounded-full blur-3xl"/>
      <div className="relative max-w-6xl mx-auto px-4 py-20 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <span className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs px-3 py-1.5 rounded-full mb-6">
            <Star size={10} fill="currentColor"/> Admissions Open 2025-26
          </span>
          <h1 className="text-white text-4xl lg:text-6xl font-extrabold leading-tight mb-5">
            Shaping <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-400">Future Leaders</span> of Tomorrow
          </h1>
          <p className="text-gray-400 text-lg leading-relaxed mb-8">A premier educational institution committed to academic excellence and holistic growth since 1985.</p>
          <div className="flex flex-wrap gap-3">
            <a href="#admissions" className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-xl font-semibold flex items-center gap-2 transition text-sm">Apply Now <ArrowRight size={16}/></a>
            <a href="#about" className="bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-xl font-semibold transition text-sm border border-gray-700">Learn More</a>
          </div>
          <div className="flex gap-8 mt-10">
            {[['2,500+','Students'],['150+','Faculty'],['40+','Years'],['98%','Pass Rate']].map(([n,l]) => (
              <div key={l}><p className="text-white text-xl font-bold">{n}</p><p className="text-gray-500 text-xs mt-0.5">{l}</p></div>
            ))}
          </div>
        </div>
        <div className="hidden lg:block">
          <div className="bg-gray-900 border border-gray-800 rounded-3xl p-6 space-y-4">
            <div className="flex items-center gap-3 bg-indigo-600/10 border border-indigo-500/20 rounded-2xl p-4">
              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shrink-0"><BookOpen size={18} className="text-white"/></div>
              <div><p className="text-white font-semibold text-sm">Smart Learning Portal</p><p className="text-gray-400 text-xs">Video classes, notes & quizzes</p></div>
            </div>
            <div className="flex items-center gap-3 bg-violet-600/10 border border-violet-500/20 rounded-2xl p-4">
              <div className="w-10 h-10 bg-violet-600 rounded-xl flex items-center justify-center shrink-0"><Users size={18} className="text-white"/></div>
              <div><p className="text-white font-semibold text-sm">Parent Connect</p><p className="text-gray-400 text-xs">Real-time progress tracking</p></div>
            </div>
            <div className="flex items-center gap-3 bg-emerald-600/10 border border-emerald-500/20 rounded-2xl p-4">
              <div className="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center shrink-0"><Trophy size={18} className="text-white"/></div>
              <div><p className="text-white font-semibold text-sm">Top Results Every Year</p><p className="text-gray-400 text-xs">98% board exam pass rate</p></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Features() {
  const features = [
    {emoji:'🎬',title:'Video Classes',desc:'Recorded + live classes accessible 24/7 on any device'},
    {emoji:'📊',title:'Smart Reports',desc:'Detailed progress reports with attendance and marks'},
    {emoji:'💳',title:'Online Fee Payment',desc:'Pay fees securely via UPI, card, or net banking'},
    {emoji:'🚌',title:'Live Bus Tracking',desc:'Parents track school bus location in real-time'},
    {emoji:'📱',title:'Mobile App',desc:'Full-featured app for Android & iOS — free download'},
    {emoji:'💬',title:'Parent-Teacher Chat',desc:'Direct messaging between parents and teachers'},
  ]
  return (
    <section id="about" className="py-20 bg-gray-950">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-white text-3xl font-bold mb-3">Why Choose Springfield Academy?</h2>
          <p className="text-gray-400 max-w-xl mx-auto">Modern technology meets traditional values</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map(f => (
            <div key={f.title} className="bg-gray-900 border border-gray-800 rounded-2xl p-5 hover:border-indigo-500/40 transition">
              <div className="text-3xl mb-3">{f.emoji}</div>
              <h3 className="text-white font-semibold mb-1.5">{f.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Admissions() {
  const [form, setForm] = useState({name:'',phone:'',email:'',grade:''})
  const [done, setDone] = useState(false)
  return (
    <section id="admissions" className="py-20 bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <h2 className="text-white text-3xl font-bold mb-4">Admissions 2025-26</h2>
          <p className="text-gray-400 mb-6 leading-relaxed">Merit-based, transparent admissions for Class 1 to 12. Scholarships for outstanding students.</p>
          <div className="space-y-4">
            {[['📅','Deadline','March 31, 2025'],['📞','Helpline','+91-9876543210'],['🏫','Timings','8:00 AM – 2:30 PM']].map(([emoji,label,value]) => (
              <div key={label as string} className="flex items-start gap-3">
                <span className="text-xl">{emoji}</span>
                <div><p className="text-gray-400 text-xs">{label}</p><p className="text-white text-sm font-medium">{value}</p></div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-gray-950 border border-gray-800 rounded-2xl p-6">
          {done ? (
            <div className="text-center py-8"><div className="text-4xl mb-3">✅</div><h3 className="text-white font-bold text-lg">Inquiry Submitted!</h3><p className="text-gray-400 text-sm mt-2">We'll contact you within 24 hours.</p></div>
          ) : (
            <>
              <h3 className="text-white font-bold text-lg mb-5">Online Inquiry Form</h3>
              <div className="space-y-4">
                {[{k:'name',l:"Student's Name",t:'text'},{k:'phone',l:'Phone',t:'tel'},{k:'email',l:'Email',t:'email'}].map(({k,l,t}) => (
                  <div key={k}><label className="block text-gray-400 text-xs mb-1">{l}</label>
                    <input type={t} value={(form as any)[k]} onChange={e => setForm({...form,[k]:e.target.value})}
                      className="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"/>
                  </div>
                ))}
                <div><label className="block text-gray-400 text-xs mb-1">Class</label>
                  <select value={form.grade} onChange={e => setForm({...form,grade:e.target.value})}
                    className="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500">
                    <option value="">Select Class</option>
                    {Array.from({length:12},(_,i) => <option key={i+1} value={`Class ${i+1}`}>Class {i+1}</option>)}
                  </select>
                </div>
                <button onClick={() => setDone(true)}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 rounded-xl transition text-sm flex items-center justify-center gap-2">
                  Submit Inquiry <ChevronRight size={16}/>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  )
}

function Contact() {
  return (
    <section id="contact" className="py-20 bg-gray-950">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-white text-3xl font-bold mb-8 text-center">Contact Us</h2>
        <div className="grid sm:grid-cols-3 gap-6 max-w-3xl mx-auto">
          {[{icon:Phone,l:'Phone',v:'+91-9876543210',s:'Mon-Sat, 9AM-5PM'},
            {icon:Mail,l:'Email',v:'info@springfield.edu',s:'Reply within 24 hours'},
            {icon:MapPin,l:'Address',v:'123 School Lane',s:'New Delhi - 110001'}
          ].map(({icon:Icon,l,v,s}) => (
            <div key={l} className="bg-gray-900 border border-gray-800 rounded-2xl p-5 text-center">
              <div className="w-10 h-10 bg-indigo-600/10 border border-indigo-500/20 rounded-xl flex items-center justify-center mx-auto mb-3"><Icon size={18} className="text-indigo-400"/></div>
              <p className="text-gray-400 text-xs mb-1">{l}</p><p className="text-white text-sm font-medium">{v}</p><p className="text-gray-500 text-xs mt-0.5">{s}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="bg-gray-950 border-t border-gray-800 py-8">
      <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center"><GraduationCap size={14} className="text-white"/></div>
          <p className="text-white text-sm font-bold">Springfield Academy</p>
        </div>
        <p className="text-gray-500 text-xs text-center">© 2025 Springfield Academy. Powered by SchoolSaaS.</p>
        <div className="flex gap-4">
          <a href="/login" className="text-gray-400 hover:text-white text-xs transition">Student Login</a>
          <a href="#admissions" className="text-gray-400 hover:text-white text-xs transition">Admissions</a>
          <a href="#contact" className="text-gray-400 hover:text-white text-xs transition">Contact</a>
        </div>
      </div>
    </footer>
  )
}

export default function PublicWebsite() {
  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar/><Hero/><Features/><Admissions/><Contact/><Footer/>
    </div>
  )
}
