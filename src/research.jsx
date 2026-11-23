import React, { useEffect, useState } from 'react'

async function requestResearch(body, signal, url) {
  const response = await fetch(url, body ? {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body), signal,
  } : { signal })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || 'The research server is unavailable.')
  if (!Array.isArray(data.schemes)) throw new Error('The research server returned an unexpected response.')
  return data
}

export function useResearch(body, url = "/api/research") {
  const key = JSON.stringify([body, url])
  const [result, setResult] = useState({})
  useEffect(() => {
    if (!body && url === "/api/research") return
    const controller = new AbortController()
    requestResearch(body, controller.signal, url).then((data) => setResult({ key, data }), (error) => {
      if (error.name !== 'AbortError') setResult({ key, error: error.message })
    })
    return () => controller.abort()
  }, [key])
  return result.key === key ? result : { loading: Boolean(body || url !== "/api/research") }
}

export function ResultState({ result, empty = 'No official scheme pages were found for this search.' }) {
  if (result.loading) return <p role="status" className="result-note"><span className="loader" /> Searching official sources through You.com…</p>
  if (result.error) return <p role="alert" className="result-note error">{result.error}</p>
  if (!result.data) return null
  return <>{result.data.warnings?.map((warning) => <p key={warning} role="status" className="result-note">{warning}</p>)}
    {!result.data.schemes.length && <p role="status" className="result-note">{empty}</p>}</>
}
