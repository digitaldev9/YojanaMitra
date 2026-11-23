import React, { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, Bookmark, ClipboardCheck, ExternalLink, FileDown, FileText } from 'lucide-react'
import { ResultState, useResearch } from './research'

const UNKNOWN = 'Not verified.'

const fields = [
  ['eligibility', 'Eligibility requirements'], ['benefits', 'Benefits'],
  ['documents', 'Required documents'], ['deadline', 'Application deadline'],
]

function OfficialLink({ scheme }) {
  return <a className="green" href={scheme.application_url || scheme.sources[0].url} target="_blank" rel="noreferrer">
    {scheme.application_url ? 'Visit official application' : 'View official details'} <ExternalLink size={16} />
  </a>
}

function ResultCards({ schemes, openDetail, matched }) {
  return <div className="results-grid">{schemes?.map((scheme) => <article className="result-card" key={scheme.sources[0].url}>
    <span className="eyebrow">{[scheme.category, scheme.scope].filter(Boolean).join(' · ')}</span>
    <h2>{scheme.name}</h2>
    <p>{scheme.description}</p>
    {matched && <div><strong>{scheme.status}</strong>
      <details><summary>Why am I matched with this scheme?</summary>
        <ul>{[...scheme.reasons, ...scheme.missing].map((reason) => <li key={reason}>{reason}</li>)}</ul>
      </details></div>}
    <div className="flex flex-wrap gap-3"><button className="green" onClick={() => openDetail(scheme)}>View Details <ArrowRight size={17} /></button>
      <a className="outline" href={scheme.sources[0].url} target="_blank" rel="noreferrer">Official source <ExternalLink size={16} /></a></div>
  </article>)}</div>
}

export function SearchResults({ t, query, category, openDetail, search }) {
  const [text, setText] = useState(query)
  const [submitted, setSubmitted] = useState(query)
  const [state, setState] = useState('')
  const [scope, setScope] = useState('')
  const [benefit, setBenefit] = useState('')
  const [page, setPage] = useState(1)
  const queryParams = new URLSearchParams({ category: category || '', q: submitted, state, scope, benefit, page })
  const endpoint = '/api/schemes' + (submitted ? '/search' : '') + '?' + queryParams
  const catalogue = useResearch(null, category ? endpoint : '/api/research')
  const live = useResearch(null, !category && query ? endpoint : '/api/research')
  const result = category ? catalogue : live
  const options = useOptions()
  const resetFilter = (setter) => (event) => { setter(event.target.value); setPage(1) }
  return <section className="inner shell">
    <a className="text-button" href="#home"><ArrowLeft size={16} /> {t('Home')}</a>
    <h1>{category ? t(category) + ' ' + t('Schemes') : t('Scheme Search')}</h1>
    {category ? <div className="panel">
      <form className="compact-form" onSubmit={(event) => { event.preventDefault(); setSubmitted(text.trim()); setPage(1) }}>
        <label>Search within {category}<input value={text} maxLength={300} placeholder="Enter a scheme name or benefit"
          onChange={(event) => { setText(event.target.value); if (!event.target.value.trim()) { setSubmitted(''); setPage(1) } }} /></label>
        <button className="green">Search</button>
        {text && <button className="outline" type="button" onClick={() => { setText(''); setSubmitted(''); setPage(1) }}>Clear</button>}
      </form>
      <div className="form-grid mt-4">
        <label>State or union territory<select value={state} onChange={resetFilter(setState)}><option value="">All states</option>
          {options.data?.state?.map((name) => <option key={name}>{name}</option>)}</select></label>
        <label>Government<select value={scope} onChange={resetFilter(setScope)}><option value="">Central and state</option><option>Central</option><option>State</option></select></label>
        <label>Benefit type<select value={benefit} onChange={resetFilter(setBenefit)}><option value="">All benefits</option>
          {result.data?.benefits?.map((name) => <option key={name}>{name}</option>)}</select></label>
      </div>
      <a className="green mt-4" href={'#eligibility?' + new URLSearchParams({ category })}>Find Schemes for Me <ArrowRight size={17} /></a>
    </div> : search}
    {result.data?.total !== undefined && <p role="status">{result.data.total} schemes found</p>}
    <ResultState result={result} empty="No verified schemes matched these filters." />
    <ResultCards schemes={result.data?.schemes} openDetail={openDetail} />
    {(category || query) && (page > 1 || result.data?.has_more) && <nav className="flex gap-3 mt-4" aria-label="Scheme pages">
      <button className="outline" disabled={page === 1 || result.loading} onClick={() => setPage(page - 1)}>Previous</button>
      <span className="self-center">Page {page}</span>
      <button className="outline" disabled={!result.data?.has_more} onClick={() => setPage(page + 1)}>Next</button>
    </nav>}
  </section>
}

function useOptions() {
  const [result, setResult] = useState({})
  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/options', { signal: controller.signal }).then((response) => {
      if (!response.ok) throw new Error('Profile options are unavailable. Check the local server and reload.')
      return response.json()
    }).then((data) => setResult({ data })).catch((error) => {
      if (error.name !== 'AbortError') setResult({ error: error.message })
    })
    return () => controller.abort()
  }, [])
  return result
}

const profileFields = [
  ['state', 'State or union territory'], ['occupation', 'Occupation'], ['education', 'Education level'],
  ['category', 'Category'], ['gender', 'Gender (optional)'], ['interest', 'Interest'],
]

export function Eligibility({ t, openDetail, category, schemeId }) {
  const { data: options, error: optionsError } = useOptions()
  const [step, setStep] = useState(1)
  const [basic, setBasic] = useState(null)
  const [profile, setProfile] = useState(null)
  const [benefit, setBenefit] = useState("")
  const benefitOptions = useResearch(null, category ? "/api/schemes?category=" + encodeURIComponent(category) + "&limit=1" : "/api/research")
  const result = useResearch(profile ? { profile, category, benefit, scheme_id: schemeId } : null, profile ? '/api/eligibility/match' : '/api/research')
  const next = (event) => {
    event.preventDefault()
    const values = Object.fromEntries(new FormData(event.currentTarget))
    setBasic({ age: Number(values.age), state: values.state, income: values.income === '' ? null : Number(values.income) })
    setStep(2)
  }
  const submit = (event) => {
    event.preventDefault()
    const values = Object.fromEntries(new FormData(event.currentTarget))
    setBenefit(values.benefit || "")
    setProfile({ ...basic, occupation: values.occupation || (category === 'Students' ? 'Student' : category === 'Farmers' ? 'Farmer' : 'Other'),
      education: values.education || 'Other', category: values.category || 'Prefer not to say',
      gender: category === 'Women' ? 'Woman' : null, interest: values.interest || 'All Schemes' })
  }
  return <section className="inner shell">
    <h1><ClipboardCheck /> {t('Eligibility Checker')}</h1>
    <p>{category ? category + ' · ' : ''}Step {step} of 2</p>
    {optionsError && <p role="alert">{optionsError}</p>}
    {!options && !optionsError && <p role="status">Loading profile options…</p>}
    {options && (step === 1 ? <form className="panel form-grid" onSubmit={next}>
      <label>Age<input name="age" type="number" min="0" max="120" required defaultValue={basic?.age ?? 18} /></label>
      <label>State or union territory<select name="state" required defaultValue={basic?.state || ''}><option value="">Select your state</option>
        {options.state.map((value) => <option key={value}>{value}</option>)}</select></label>
      <label>Annual family income (₹, optional)<input name="income" type="number" min="0" max="1000000000" defaultValue={basic?.income ?? ''} /></label>
      <button className="green">Continue <ArrowRight size={17} /></button>
    </form> : <form className="panel form-grid" onSubmit={submit}>
      {profileFields.filter(([key]) => key === 'category' || (key === 'education' && (!category || category === 'Students')) ||
        (key === 'occupation' && (!category || category === 'Women')) || (key === 'interest' && !category)).map(([key, label]) => <label key={key}>{label}
          <select name={key} defaultValue={profile?.[key] || ''}><option value="">Prefer not to say</option>
            {options[key].filter((value) => value !== 'Prefer not to say').map((value) => <option key={value}>{value}</option>)}</select>
        </label>)}
      {category && <label>What help are you looking for?<select name="benefit" defaultValue={benefit}>
        <option value="">All benefits</option>
        {benefitOptions.data?.benefits?.map((value) => <option key={value}>{value}</option>)}
      </select></label>}
      <div className="flex gap-3"><button type="button" className="outline" onClick={() => setStep(1)}>Back</button>
        <button className="green" disabled={result.loading}>Find matching schemes</button></div>
    </form>)}
    <ResultState result={result} empty="No catalogue schemes matched this selection." />
    {[['Likely Eligible', /^Likely/], ['More Information Needed', /^Possibly/], ['Not Eligible', /^Not Eligible/]].map(([label, pattern]) => {
      const items = result.data?.schemes.filter((scheme) => pattern.test(scheme.status))
      return items?.length ? <section key={label} className="mt-4"><h2>{label} ({items.length})</h2><ResultCards schemes={items} openDetail={openDetail} matched /></section> : null
    })}
  </section>
}

function useScheme(name, scheme, schemeId) {
  const result = useResearch(name && !scheme && !schemeId ? { mode: 'search', query: name } : null, !scheme && schemeId ? '/api/schemes/' + encodeURIComponent(schemeId) : '/api/research')
  const match = result.data?.schemes.find((item) => item.name.toLowerCase() === name.toLowerCase())
  return [scheme || match, result]
}

export function SchemeDetail({ t, name, scheme, schemeId, isSaved, toggleSaved }) {
  const [selected, result] = useScheme(name, scheme, schemeId)
  const full = useResearch(selected ? { mode: 'details', query: selected.name, source: selected.sources[0]?.url, scheme_id: selected.id } : null)
  const details = full.data?.details
  const sources = [...(details?.sources || []), ...(selected?.sources || [])]
    .filter((source, index, list) => list.findIndex((item) => item.url === source.url) === index)
  const sections = details?.sections || {}
  const tables = details?.tables || []
  const application = details?.application_url || selected?.application_url
  return <section className="inner shell">
    <a href="#home" className="text-button"><ArrowLeft size={16} /> {t('Home')}</a>
    <h1>{name || t('Scheme details')}</h1>
    {!selected ? <ResultState result={result} /> : <div className="panel detail">
      <span className="eyebrow">{[selected.category, selected.scope, selected.department].filter(Boolean).join(' · ')}</span>
      {full.loading && <p role="status">Loading details from official sources…</p>}
      {!full.loading && (!details?.sources.length || full.error) && <p>Full details could not be loaded. The available search information is shown below.</p>}
      {selected.last_verified && <p>Official source checked {selected.last_verified}</p>}
      {selected.reasons?.length > 0 && <section><h2>Your eligibility result</h2><strong>{selected.status}</strong>
        <ul>{[...selected.reasons, ...selected.missing].map((reason, index) => <li key={index}>{reason}</li>)}</ul></section>}
      <h2>Overview</h2>
      {(sections.overview || [selected.description]).map((line, index) => <p key={index}>{line}</p>)}
      <div className="form-grid">
        {[['audience', 'Who it is for'], ...fields, ['timing', 'When to apply'], ['steps', 'How to apply']].map(([id, label]) => {
          const items = sections[id] || selected.fields[id]
          const sectionTables = tables.filter((table) => table.section === id)
          return <section key={id}><h2>{label}</h2>
            {items?.length ? <ul>{items.map((line, index) => <li key={index}>{line}</li>)}</ul> : !sectionTables.length && <p>{UNKNOWN}</p>}
            {sectionTables.map((table, index) => <div key={index} style={{ overflowX: 'auto' }}>
              <table className="w-full text-left border-collapse"><thead><tr>{table.headers.map((cell, column) => <th className="border p-2" scope="col" key={column}>{cell}</th>)}</tr></thead>
                <tbody>{table.rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, column) => <td className="border p-2" key={column}>{cell}</td>)}</tr>)}</tbody>
              </table>
            </div>)}
          </section>
        })}
      </div>
      <h2>Official website and portal</h2>
      {details?.portal_url && <p><a className="text-button" href={details.portal_url} target="_blank" rel="noreferrer">Scheme listing on MahaDBT <ExternalLink size={16} /></a></p>}
      <ul>{sources.map((source) => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.title}</a></li>)}</ul>
      <div className="flex flex-wrap gap-3">
        {application && <a className="green" href={application} target="_blank" rel="noreferrer">Apply on official portal <ExternalLink size={16} /></a>}
        <a className="outline" href={'#eligibility?' + new URLSearchParams(selected.id ? { id: selected.id } : {})}>Check My Eligibility</a>
        <a className="outline" href={'#application?' + new URLSearchParams({ name: selected.name, ...(selected.id ? { id: selected.id } : {}) })}><FileText size={17} /> Prepare My Application</a>
        <button className="outline" aria-pressed={isSaved(selected)} onClick={() => toggleSaved(selected)}><Bookmark size={17} /> {isSaved(selected) ? 'Saved' : 'Save scheme'}</button>
      </div>
    </div>}
    {!selected && result.data?.schemes.length > 0 && <p>We couldn’t verify the exact scheme in this search. Return to the homepage to search again.</p>}
  </section>
}

export function Application({ t, name, scheme, schemeId }) {
  const [query, setQuery] = useState('')
  const [request, setRequest] = useState('')
  const [picked, setPicked] = useState(null)
  const [selected, detailResult] = useScheme(name, scheme, schemeId)
  const matches = useResearch(request ? { mode: 'search', query: request } : null)
  const target = picked || selected
  const [review, setReview] = useState(null)
  const full = useResearch(target ? { mode: 'details', query: target.name, source: target.sources[0]?.url, scheme_id: target.id } : null)
  const details = full.data?.details
  const documents = details?.sections?.documents || target?.fields.documents || []
  const prepare = (event) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setReview({ name: target.name, applicant: form.get('applicant').trim(), state: form.get('state').trim(),
      notes: form.get('notes'), documents: documents.map((item) => ({ item, checked: form.getAll('document').includes(item) })) })
  }
  return <section className="inner shell">
    <h1><FileText /> {t('Application Assistant')}</h1>
    <p>Prepare a checklist on this device, then use the official website to complete your application.</p>
    {!target && <>
      <ResultState result={detailResult} />
      <form className="panel compact-form" onSubmit={(event) => { event.preventDefault(); setRequest(query.trim()) }}>
        <label>Find the scheme you’re applying for<input minLength={2} maxLength={300} required value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Enter a scheme name" /></label>
        <button className="green">Find scheme <ArrowRight size={17} /></button>
      </form>
      <ResultState result={matches} />
      {matches.data?.schemes.map((item) => <button className="outline m-1" key={item.sources[0].url} onClick={() => setPicked(item)}>{item.name}</button>)}
    </>}
    {target && <div className="panel detail">
      <h2>{target.name}</h2>
      <p>{target.description}</p>
      <OfficialLink scheme={target} />
      <form onSubmit={prepare} className="form-grid mt-5">
        <label>Applicant name<input name="applicant" required minLength={2} maxLength={100} /></label>
        <label>State or union territory<input name="state" required minLength={2} maxLength={100} /></label>
        <label className="full">Preparation notes (optional)<textarea name="notes" maxLength={1000} /></label>
        <fieldset className="full"><legend>Published documents</legend>
          {documents.length ? documents.map((item) => <label className="check" key={item}><input type="checkbox" name="document" value={item} />{item}</label>)
            : <p>{UNKNOWN} Review the official source for a complete list.</p>}
        </fieldset>
        <button className="green"><FileDown size={17} /> Review application checklist</button>
      </form>
    </div>}
    {review && <section className="panel application-print" aria-label="Application review">
      <h2>{review.name}</h2>
      <p>Applicant: {review.applicant}</p><p>State: {review.state}</p><p>{review.notes}</p>
      <ul>{review.documents.map(({ item, checked }, index) => <li key={index}>{checked ? 'Ready: ' : 'Pending: '}{item}</li>)}</ul>
      <button className="green print-hide mt-4" onClick={() => window.print()}><FileDown size={17} /> Print or Save as PDF</button>
    </section>}
  </section>
}

export function About({ t }) {
  return <section className="inner shell">
    <h1>{t('About YojanaMitra')}</h1>
    <div className="panel detail">
      <p>YojanaMitra helps people discover Indian government schemes. It uses You.com to find official pages and highlights, then shows the available eligibility, benefits, documents and application details with source links.</p>
      <p>Eligibility Checker compares explicit published rules with your profile. Application Assistant prepares a checklist you can download and use with the official application.</p>
      <p>Confirm eligibility, deadlines and application procedures with the relevant government department.</p>
    </div>
  </section>
}
