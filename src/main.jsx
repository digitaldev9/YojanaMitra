import React, { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { MotionConfig, motion } from 'framer-motion'
import { ArrowRight, Bookmark, Bot, ChevronDown, ExternalLink, Globe, Menu, Mic, Search, Send, Sprout, Star, UserRound, X } from 'lucide-react'
import { categories, features, languages, schemeIcons, suggestions, translate } from './content'
import { About, Application, Eligibility, SchemeDetail, SearchResults } from './pages'
import '@fontsource-variable/inter'
import { ResultState, useResearch } from './research'
import './styles.css'

const makeRoute = (page, params = {}) => '#' + page + (Object.keys(params).length ? '?' + new URLSearchParams(params) : '')
const searchRoute = (query, category) => makeRoute('results', category ? { category } : { q: query })
const ALL_QUERY = 'government schemes national state scholarships welfare agriculture skills'
const getRoute = () => {
  const [page, raw] = (location.hash.slice(1) || 'home').split('?')
  return { page, params: new URLSearchParams(raw) }
}
const readLocal = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback } catch { return fallback }
}
const persist = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* browser storage is optional */ } }

function SearchBar({ t, voice, onSearch, initial = '', inputRef }) {
  const [query, setQuery] = useState(initial)
  return <form className="searchbar" role="search" onSubmit={(event) => {
    event.preventDefault()
    if (query.trim().length >= 2) onSearch(query.trim())
  }}>
    <Search className="search-symbol" size={29} aria-hidden />
    <input ref={inputRef} aria-label={t('Search')} placeholder={t('Search any scheme... e.g. scholarship for students, loan for women, farm subsidy')}
      value={query} onChange={(event) => setQuery(event.target.value)} minLength={2} maxLength={300} required />
    <button className="circle mic" type="button" aria-label={t('Voice Search')} onClick={() => voice((spoken) => { setQuery(spoken); onSearch(spoken) })}><Mic size={23} /></button>
    <button className="green search-submit" type="submit"><Search size={20} /> {t('Search')}</button>
  </form>
}

function Header({ t, language, setLanguage, voice, onSearch, profile, openAccount, route, languageRef }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)
  useEffect(() => {
    function close(event) { if (!menuRef.current?.contains(event.target)) setMenuOpen(false) }
    document.addEventListener('pointerdown', close)
    return () => document.removeEventListener('pointerdown', close)
  }, [])
  const closeNav = () => { setMobileOpen(false); setMenuOpen(false) }
  return <header className="topbar">
    <div className="navbar">
      <a className="brand" href="#home" onClick={closeNav} aria-label="YojanaMitra home">
        <span className="brand-mark"><Sprout size={49} strokeWidth={2.8} /></span>
        <span><strong>Yojana<span>Mitra</span></strong><small>{t('Your Guide to Government Schemes')}</small></span>
      </a>
      <button className="circle mobile-menu" aria-label="Toggle navigation" aria-expanded={mobileOpen} onClick={() => setMobileOpen(!mobileOpen)}><Menu /></button>
      <nav aria-label="Main navigation" className={mobileOpen ? 'nav-links open' : 'nav-links'}>
        <a href="#home" className={route === 'home' ? 'active' : ''} onClick={closeNav}>{t('Home')}</a>
        <div className="nav-dropdown" ref={menuRef} onKeyDown={(event) => { if (event.key === 'Escape') setMenuOpen(false) }}>
          <button aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}>{t('Schemes')} <ChevronDown size={16} /></button>
          {menuOpen && <div className="schemes-menu">
            <a href={searchRoute(ALL_QUERY)} onClick={closeNav}>{t('View All Schemes')}</a>
            {categories.map((category) => <a key={category.name} href={searchRoute(category.query, category.name)} onClick={closeNav}>{t(category.name)}</a>)}
          </div>}
        </div>
        <a href="#eligibility" onClick={closeNav}>{t('Eligibility Checker')}</a>
        <a href="#application" onClick={closeNav}>{t('Application Assistant')}</a>
        <a href="#about" onClick={closeNav}>{t('About')}</a>
      </nav>
      <div className="nav-actions">
        <label className="language-control"><Globe size={17} /><select ref={languageRef} aria-label="Language" value={language} onChange={(event) => setLanguage(event.target.value)}>
          {Object.entries(languages).map(([code, [name]]) => <option key={code} value={code}>{name}</option>)}
        </select><ChevronDown size={14} /></label>
        <button className="circle header-mic" aria-label={t('Voice Search')} onClick={() => voice(onSearch)}><Mic size={20} /></button>
        <button className="green account" aria-label={profile || t('Login / Sign Up')} onClick={openAccount}><UserRound size={18} /> <span>{profile || t('Login / Sign Up')}</span></button>
      </div>
    </div>
  </header>
}

function Home({ t, voice, onSearch, openDetail, languageRef }) {
  const featured = useResearch({ mode: 'featured' })
  const input = useRef(null)
  const featureAction = { search: () => input.current?.focus(), language: () => languageRef.current?.focus(), voice: () => voice(onSearch) }
  return <>
    <section className="hero">
      <div className="hero-landscape" aria-hidden />
      <motion.div className="hero-intro" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.38 }}>
        <span className="hero-badge"><span className="india-flag" aria-hidden /> {t('Government Scheme Discovery Platform')}</span>
        <h1>{t('Discover Government Schemes')}<br />{t('Made for You')}</h1>
        <p>{t('Find, understand, and apply for government schemes easily with AI.')}</p>
      </motion.div>
      <SearchBar t={t} voice={voice} onSearch={onSearch} inputRef={input} />
      <div className="popular"><strong>{t('Popular Searches')}:</strong>
        {suggestions.map(([label, Icon, color]) => <a className={'chip ' + color} key={label} href={searchRoute(label)}><Icon size={17} />{t(label)}</a>)}
      </div>
      <div className="categories shell">
        {categories.map(({ name, theme, icon: Icon, description, query }, index) => (
          <motion.a key={name} className={'category-card ' + theme} href={searchRoute(query, name)}
            initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.34, delay: index * 0.05 }} whileHover={{ y: -5, rotateX: 2 }}>
            <div className="portrait" aria-hidden />
            <div className="category-copy"><Icon size={43} strokeWidth={2.1} />
              <h2>{t(name)}</h2><p>{t(description)}</p>
              <span className="explore">{t('Explore Schemes')} <ArrowRight size={17} /></span>
            </div>
          </motion.a>
        ))}
      </div>
    </section>
    <section className="features shell" aria-label="Quick features">
      {features.map(([label, sub, Icon, theme, action]) => {
        const content = <><span className={'feature-icon ' + theme}><Icon size={27} /></span><strong>{t(label)}</strong>{sub && <small>{t(sub)}</small>}</>
        return featureAction[action]
          ? <button className="feature" key={action} onClick={featureAction[action]}>{content}</button>
          : <a className="feature" key={action} href={'#' + action}>{content}</a>
      })}
    </section>
    <section className="featured shell">
      <div className="featured-top"><div><h2><Star size={25} fill="currentColor" />{t('Featured Government Schemes')}</h2><p>{t('Explore some important and widely available government schemes.')}</p></div>
        <a href={searchRoute(ALL_QUERY)}>{t('View All Schemes')} <ArrowRight size={17} /></a></div>
      <ResultState result={featured} empty="No scheme pages were found in this featured search." />
      <div className="featured-grid">
        {featured.data?.schemes.slice(0, 3).map((scheme, index) => {
          const Icon = schemeIcons[index]
          return <article className={'featured-card ' + categories[index].theme} key={scheme.sources[0].url}>
            <h3><Icon size={24} />{scheme.name}</h3>
            <p>{scheme.description}</p><p>{scheme.fields.eligibility?.[0]}</p><p>{scheme.fields.benefits?.[0]}</p>
            <button className="text-button" onClick={() => openDetail(scheme)}>{t('View Details')} <ArrowRight size={16} /></button>
          </article>
        })}
      </div>
    </section>
  </>
}

function Chat({ t, openDetail }) {
  const [open, setOpen] = useState(() => window.innerWidth >= 900)
  const [query, setQuery] = useState('')
  const [request, setRequest] = useState(null)
  const [context, setContext] = useState('')
  const result = useResearch(request)
  const send = (value, followUp = false) => {
    const clean = value.trim()
    if (clean.length < 2) return
    const search = followUp && context ? 'Required documents for ' + context : clean
    setRequest({ mode: 'chat', query: search.slice(0, 300) })
    if (!followUp) setContext(clean)
    setQuery('')
  }
  if (!open) return <button className="chat-launch green" aria-label="Open YojanaMitra" onClick={() => setOpen(true)}><Bot size={25} /> YojanaMitra</button>
  const isDocuments = request && /document/i.test(request.query)
  return <aside className="chat" aria-label="YojanaMitra">
    <div className="chat-head"><img className="bot-avatar" src="/art/saathi.webp" alt="" /><div><h2>YojanaMitra</h2><p>{t('Your AI Government Scheme Assistant')}</p></div>
      <button className="plain-icon" aria-label="Close assistant" onClick={() => setOpen(false)}><X size={20} /></button></div>
    <div className="chat-body" aria-live="polite">
      <p className="chat-bubble">{t('How can I help you today?')}</p>
      <div className="chat-actions">
        <a href="#eligibility" onClick={() => setOpen(false)}>{t('Find schemes for me')}</a>
        <a href="#eligibility" onClick={() => setOpen(false)}>{t('Check my eligibility')}</a>
        <a href="#application" onClick={() => setOpen(false)}>{t('How to apply?')}</a>
        <button onClick={() => { if (context) send('Required documents', true); else setQuery('Required documents for ') }}>{t('Required documents')}</button>
      </div>
      {request && <p className="chat-query">{request.query}</p>}
      <ResultState result={result} empty="No matching official scheme page was found. Try entering the full scheme name." />
      {result.data?.schemes.slice(0, 2).map((scheme) => <article className="chat-answer" key={scheme.sources[0].url}>
        <button className="text-button" onClick={() => { openDetail(scheme); setOpen(false) }}>{scheme.name}</button>
        <p>{isDocuments ? (scheme.fields.documents?.slice(0, 3).join(' ') || 'Documents were unavailable in the retrieved excerpts. Check the official source.') : scheme.description}</p>
        <a href={scheme.sources[0].url} target="_blank" rel="noreferrer">Official source <ExternalLink size={13} /></a>
      </article>)}
    </div>
    <form className="chat-form" onSubmit={(event) => { event.preventDefault(); send(query) }}>
      <input aria-label="Message" value={query} maxLength={300} minLength={2} required onChange={(event) => setQuery(event.target.value)} placeholder={t('Ask anything about schemes...')} />
      <button aria-label="Send message"><Send size={21} /></button>
    </form>
  </aside>
}

function Account({ name, onSave, onClose }) {
  const dialog = useRef(null)
  const [draft, setDraft] = useState(name)
  useEffect(() => { dialog.current.showModal() }, [])
  return <dialog ref={dialog} className="account-dialog" onClose={onClose}>
    <div className="flex items-center justify-between gap-4"><h2>Device profile</h2><button className="plain-icon" aria-label="Close" onClick={onClose}><X /></button></div>
    <p>Use a name to keep your saved schemes separate on this browser. This profile stays on this device.</p>
    <form onSubmit={(event) => { event.preventDefault(); if (draft.trim()) onSave(draft.trim()) }}>
      <label>Display name<input value={draft} onChange={(event) => setDraft(event.target.value)} required maxLength={40} autoFocus /></label>
      <div className="flex flex-wrap gap-3"><button className="green" type="submit">{name ? 'Update profile' : 'Continue on this device'}</button>
        {name && <button className="outline" type="button" onClick={() => onSave('')}>Sign out</button>}</div>
    </form>
  </dialog>
}

function App() {
  const [route, setRoute] = useState(getRoute)
  const [language, setLanguage] = useState(() => {
    const stored = readLocal('ys-language', 'en')
    return Object.hasOwn(languages, stored) ? stored : 'en'
  })
  const [profile, setProfile] = useState(() => readLocal('ys-profile', ''))
  const [showAccount, setShowAccount] = useState(false)
  const [detail, setDetail] = useState(null)
  const [voiceStatus, setVoiceStatus] = useState('')
  const languageRef = useRef(null)
  const recognizer = useRef(null)
  const t = (label) => translate(language, label)
  const savedKey = 'ys-saved:' + profile
  const [savedByProfile, setSavedByProfile] = useState({})
  const saved = savedByProfile[savedKey] || readLocal(savedKey, [])
  const isSaved = (scheme) => saved.some((item) => item.sources[0].url === scheme.sources[0].url)
  const toggleSaved = (scheme) => {
    const next = isSaved(scheme) ? saved.filter((item) => item.sources[0].url !== scheme.sources[0].url) : [...saved, scheme]
    persist(savedKey, next)
    setSavedByProfile({ ...savedByProfile, [savedKey]: next })
  }
  const trackSaved = (scheme, progress) => {
    const next = saved.map((item) => item.sources[0].url === scheme.sources[0].url ? { ...item, progress } : item)
    persist(savedKey, next)
    setSavedByProfile({ ...savedByProfile, [savedKey]: next })
  }
  useEffect(() => {
    const update = () => { setRoute(getRoute()); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', update)
    return () => window.removeEventListener('hashchange', update)
  }, [])
  useEffect(() => { document.documentElement.lang = language }, [language])
  const onSearch = (value) => {
    location.hash = makeRoute('results', { q: value, attempt: Date.now() })
  }
  const openDetail = (scheme) => {
    setDetail(scheme)
    location.hash = makeRoute('detail', { name: scheme.name, ...(scheme.id ? { id: scheme.id } : {}) })
  }
  function voice(callback) {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!Recognition) { setVoiceStatus('Voice search is unavailable in this browser. You can type your search instead.'); return }
    if (recognizer.current) { recognizer.current.abort(); return }
    const instance = new Recognition()
    recognizer.current = instance
    instance.lang = languages[language][1]
    instance.onstart = () => setVoiceStatus('Listening…')
    instance.onresult = (event) => {
      setVoiceStatus('')
      const spoken = event.results[0][0].transcript.trim().slice(0, 300)
      if (spoken.length >= 2) callback(spoken)
    }
    instance.onerror = (event) => setVoiceStatus(event.error === 'aborted' ? '' : 'Voice search could not start. Check microphone permissions or type your search.')
    instance.onend = () => { recognizer.current = null; setVoiceStatus((status) => status === 'Listening…' ? '' : status) }
    try { instance.start() } catch { recognizer.current = null; setVoiceStatus('Voice search could not start. You can type your search instead.') }
  }
  const { page, params } = route
  const query = params.get('q') || ''
  const detailName = params.get('name') || ''
  const schemeId = params.get('id') || ''
  const currentDetail = detail?.name === detailName ? detail : saved.find((scheme) => scheme.name === detailName)
  return <MotionConfig reducedMotion="user">
    <a className="skip-link" href="#main-content" onClick={(event) => { event.preventDefault(); document.getElementById('main-content')?.focus() }}>Skip to main content</a>
    <Header t={t} language={language} setLanguage={(next) => { setLanguage(next); persist('ys-language', next) }} voice={voice}
      onSearch={onSearch} profile={profile} openAccount={() => setShowAccount(true)} route={page} languageRef={languageRef} />
    {voiceStatus && <div className="voice-status" role="status">{voiceStatus}<button className="plain-icon" aria-label="Dismiss voice status" onClick={() => { recognizer.current?.abort(); setVoiceStatus('') }}><X size={18} /></button></div>}
    <main id="main-content" tabIndex={-1}>
      {page === 'home' && <Home t={t} voice={voice} onSearch={onSearch} openDetail={openDetail} languageRef={languageRef} />}
      {page === 'results' && <SearchResults key={params.toString()} t={t} query={query} category={params.get('category')} openDetail={openDetail}
        search={<SearchBar t={t} voice={voice} onSearch={onSearch} initial={query} />} />}
      {page === 'eligibility' && <Eligibility key={params.toString()} t={t} openDetail={openDetail} category={params.get("category")} schemeId={schemeId} />}
      {page === 'application' && <Application t={t} schemeId={schemeId} name={detailName} scheme={currentDetail} />}
      {page === 'detail' && <SchemeDetail t={t} schemeId={schemeId} name={detailName} scheme={currentDetail} isSaved={isSaved} toggleSaved={toggleSaved} />}
      {page === 'about' && <About t={t} />}
      {page === 'saved' && <section className="inner shell"><h1><Bookmark /> {t('Saved schemes')}</h1>
        {saved.length ? <div className="results-grid">{saved.map((scheme) => <article className="result-card" key={scheme.sources[0].url}>
          <h2>{scheme.name}</h2>
          <label className="tracking">Application progress
            <select value={scheme.progress || 'Saved'} onChange={(event) => trackSaved(scheme, event.target.value)}>
              {['Saved', 'Preparing', 'Submitted', 'Completed'].map((progress) => <option key={progress}>{progress}</option>)}
            </select>
          </label>
          <div className="flex flex-wrap gap-3"><button className="green" onClick={() => openDetail(scheme)}>View Details</button>
            <button className="outline" onClick={() => toggleSaved(scheme)}>Remove</button></div>
        </article>)}</div> : <p>Save a scheme from its detail page to track it here.</p>}</section>}
      {!['home', 'results', 'eligibility', 'application', 'detail', 'about', 'saved'].includes(page) && <section className="inner shell"><h1>Page unavailable</h1><a href="#home">Return home</a></section>}
    </main>
    <footer>YojanaMitra is an independent discovery assistant. Verify application requirements on the official source.</footer>
    <Chat t={t} openDetail={openDetail} />
    {showAccount && <Account name={profile} onClose={() => setShowAccount(false)} onSave={(name) => { setProfile(name); persist('ys-profile', name); setShowAccount(false) }} />}
  </MotionConfig>
}

createRoot(document.getElementById('root')).render(<App />)
