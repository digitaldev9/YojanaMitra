import React, { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, Bookmark, ClipboardCheck, ExternalLink, FileDown, FileText } from 'lucide-react'
import { ResultState, useResearch } from './research'

const UNKNOWN = 'Not confirmed from available sources.'

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
  const result = useResearch(query ? { mode: 'search', query, category } : null)
  return <section className="inner shell">
    <a className="text-button" href="#home"><ArrowLeft size={16} /> {t('Home')}</a>
    <h1>{category ? t(category) + ' ' + t('Schemes') : t('Scheme Search')}</h1>
    {search}
    {query && <p className="search-summary">Results for “{query}”</p>}
    <ResultState result={result} />
    <ResultCards schemes={result.data?.schemes} openDetail={openDetail} />
  </section>
}

const profileFields = [
  ['state', 'State or union territory'], ['occupation', 'Occupation'], ['education', 'Education level'],
  ['category', 'Category'], ['gender', 'Gender (optional)'], ['interest', 'Interest'],
]

export function Eligibility({ t, openDetail }) {
  const [options, setOptions] = useState(null)
  const [optionsError, setOptionsError] = useState('')
  const [profile, setProfile] = useState(null)
  const result = useResearch(profile ? { mode: 'eligibility', profile } : null)
  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/options', { signal: controller.signal }).then((response) => {
      if (!response.ok) throw new Error('Profile options are unavailable. Check the local server and reload.')
      return response.json()
    }).then(setOptions).catch((error) => { if (error.name !== 'AbortError') setOptionsError(error.message) })
    return () => controller.abort()
  }, [])
  const submit = (event) => {
    event.preventDefault()
    const form = Object.fromEntries(new FormData(event.currentTarget))
    setProfile({ ...form, age: Number(form.age), income: form.income === '' ? null : Number(form.income), gender: form.gender || null })
  }
  return <section className="inner shell">
    <h1><ClipboardCheck /> {t('Eligibility Checker')}</h1>
    <p>Compare your profile with published eligibility conditions. The official scheme administrator makes the final decision.</p>
    {optionsError ? <p role="alert" className="result-note error">{optionsError}</p> : null}
    {!options && !optionsError && <p role="status">Loading profile options…</p>}
    {options && <form className="panel form-grid" onSubmit={submit}>
      <label>{t('Age')}<input name="age" type="number" min="0" max="120" step="1" required defaultValue="18" /></label>
      <label>{t('Annual family income (₹, optional)')}<input name="income" type="number" min="0" max="1000000000" step="1" /></label>
      {profileFields.map(([key, label]) => <label key={key}>{t(label)}
        <select name={key} defaultValue={key === 'category' ? 'Prefer not to say' : ''} required={key !== 'gender'}>
          <option value="">{key === 'gender' ? 'Unspecified' : 'Select an option'}</option>
          {options[key]?.map((value) => <option key={value}>{value}</option>)}
        </select>
      </label>)}
      <button className="green" disabled={result.loading}>{t('Find matching schemes')} <ArrowRight size={17} /></button>
    </form>}
    <ResultState result={result} />
    <ResultCards schemes={result.data?.schemes} openDetail={openDetail} matched />
  </section>
}

function useScheme(name, scheme) {
  const result = useResearch(name && !scheme ? { mode: 'search', query: name } : null)
  const match = result.data?.schemes.find((item) => item.name.toLowerCase() === name.toLowerCase())
  return [scheme || match, result]
}

export function SchemeDetail({ t, name, scheme, isSaved, toggleSaved }) {
  const [selected, result] = useScheme(name, scheme)
  const full = useResearch(selected ? { mode: 'details', query: selected.name, source: selected.sources[0]?.url } : null)
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
        <a className="outline" href={'#application?' + new URLSearchParams({ name: selected.name })}><FileText size={17} /> Prepare application</a>
        <button className="outline" aria-pressed={isSaved(selected)} onClick={() => toggleSaved(selected)}><Bookmark size={17} /> {isSaved(selected) ? 'Saved' : 'Save scheme'}</button>
      </div>
    </div>}
    {!selected && result.data?.schemes.length > 0 && <p>We couldn’t verify the exact scheme in this search. Return to the homepage to search again.</p>}
  </section>
}

export function Application({ t, name, scheme }) {
  const [query, setQuery] = useState('')
  const [request, setRequest] = useState('')
  const [picked, setPicked] = useState(null)
  const [selected, detailResult] = useScheme(name, scheme)
  const matches = useResearch(request ? { mode: 'search', query: request } : null)
  const target = picked || selected
  const download = (event) => {
    event.preventDefault()
    if (!target) return
    const form = new FormData(event.currentTarget)
    const completed = form.getAll('document')
    const checklist = (target.fields.documents || []).map((document) => (completed.includes(document) ? '☑ ' : '☐ ') + document)
    const text = ['YojanaSetu application preparation', target.name, 'Applicant: ' + form.get('applicant'),
      'State: ' + form.get('state'), 'Notes: ' + form.get('notes'), '', ...checklist, '',
      'Official source: ' + (target.application_url || target.sources[0].url)].join('\n')
    const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'yojanasetu-application-checklist.txt'
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
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
      <form onSubmit={download} className="form-grid mt-5">
        <label>Applicant name<input name="applicant" required minLength={2} maxLength={100} /></label>
        <label>State or union territory<input name="state" required minLength={2} maxLength={100} /></label>
        <label className="full">Preparation notes (optional)<textarea name="notes" maxLength={1000} /></label>
        <fieldset className="full"><legend>Published documents</legend>
          {target.fields.documents?.length ? target.fields.documents.map((item) => <label className="check" key={item}><input type="checkbox" name="document" value={item} />{item}</label>)
            : <p>{UNKNOWN} Review the official source for a complete list.</p>}
        </fieldset>
        <button className="green"><FileDown size={17} /> Download preparation checklist</button>
      </form>
    </div>}
  </section>
}

export function About({ t }) {
  return <section className="inner shell">
    <h1>{t('About YojanaSetu')}</h1>
    <div className="panel detail">
      <p>YojanaSetu helps people discover Indian government schemes. It uses You.com to find official pages and highlights, then shows the available eligibility, benefits, documents and application details with source links.</p>
      <p>Eligibility Checker compares explicit published rules with your profile. Application Assistant prepares a checklist you can download and use with the official application.</p>
      <p>Confirm eligibility, deadlines and application procedures with the relevant government department.</p>
    </div>
  </section>
}
