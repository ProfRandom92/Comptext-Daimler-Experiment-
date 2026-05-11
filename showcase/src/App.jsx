import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'

const DEFAULT_TEXT = `Wartungsauftrag 2026-05-11
Fahrzeug: eCitaro Testflotte
FIN: WDB906232N3123456
Kilometerstand: 145000 km
Fehlercode: P0300 - Zündaussetzer Zylinder 1
Zusatz: Kunde meldet Leistungsverlust nach Werkstatt-Testfahrt
Maßnahme: Zündkerzen prüfen, Sensorwerte vergleichen, Diagnose sichern`

const apiCards = [
  { label: 'Health', path: '/health', method: 'GET', tone: 'good' },
  { label: 'Analyze', path: '/analyze', method: 'POST', tone: 'accent' },
  { label: 'Benchmark', path: '/benchmark', method: 'GET', tone: 'info' },
  { label: 'Docs', path: '/docs', method: 'GET', tone: 'muted' },
]

const evidence = [
  'Synthetic-only showcase payloads',
  'FastAPI health endpoint preserved',
  'Docker image bundles React build',
  'Render entrypoint tested in CI',
]

const scenarios = [
  {
    title: 'XENTRY diagnostic compression',
    metric: 'fault-focused',
    body: 'Condenses repetitive workshop and diagnostic logs into compact KVTC frames for review and replay.',
  },
  {
    title: 'MO360 shift signal filtering',
    metric: 'noise-aware',
    body: 'Separates production-shift deviations from routine status chatter using deterministic synthetic fixtures.',
  },
  {
    title: 'Supply-chain deduplication',
    metric: 'semantic merge',
    body: 'Groups repeated supplier updates before downstream analysis without requiring real customer payloads.',
  },
]

function formatJson(value) {
  return JSON.stringify(value, null, 2)
}

function ResultPanel({ status, result, error }) {
  if (error) {
    return <pre className="result error">{error}</pre>
  }
  if (result) {
    return <pre className="result">{formatJson(result)}</pre>
  }
  return (
    <div className="empty-result">
      <span>Ready</span>
      <p>Run the synthetic analysis request to verify the deployed API and showcase connection.</p>
    </div>
  )
}

export default function App() {
  const [text, setText] = useState(DEFAULT_TEXT)
  const [source, setSource] = useState('Werkstatt-SAP')
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const tokenEstimate = useMemo(() => Math.max(1, Math.round(text.trim().split(/\s+/).filter(Boolean).length * 1.25)), [text])

  async function analyze() {
    setStatus('loading')
    setError('')
    setResult(null)
    try {
      const response = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, quelle: source }),
      })
      const payload = await response.json()
      if (!response.ok) throw new Error(formatJson(payload))
      setResult(payload)
      setStatus('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setStatus('error')
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <nav className="topbar">
          <div className="brand-lockup">
            <span className="brand-mark">CT</span>
            <div>
              <strong>CompText Daimler Experiment</strong>
              <small>Synthetic benchmark and showcase environment</small>
            </div>
          </div>
          <div className="nav-actions">
            <a href="/health">Health</a>
            <a href="/docs">API Docs</a>
            <a href="/benchmark">Benchmark</a>
          </div>
        </nav>

        <div className="hero-grid">
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
            <p className="eyebrow">Render-ready industrial AI middleware</p>
            <h1>Token compression, triage, and safe diagnostic replay.</h1>
            <p className="hero-copy">
              A polished synthetic showcase for CompText/KVTC workflows: FastAPI endpoints,
              React frontend, Docker deployment, benchmark gates, and no real Daimler payloads.
            </p>
            <div className="hero-actions">
              <button onClick={analyze} disabled={status === 'loading'}>{status === 'loading' ? 'Analyzing…' : 'Run synthetic demo'}</button>
              <a href="#demo">Open workbench</a>
            </div>
          </motion.div>

          <motion.aside className="signal-card" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.45, delay: 0.08 }}>
            <span className="status-pill">Live deployment</span>
            <div className="signal-metric">94%</div>
            <p>Target compression posture for structured synthetic diagnostics.</p>
            <div className="signal-grid">
              <span>Docker</span><strong>bundled UI</strong>
              <span>API</span><strong>FastAPI</strong>
              <span>Data</span><strong>synthetic</strong>
            </div>
          </motion.aside>
        </div>
      </section>

      <section className="content-grid">
        <article className="card span-2">
          <div className="section-heading">
            <p className="eyebrow">System overview</p>
            <h2>One service, two surfaces</h2>
          </div>
          <div className="pipeline">
            <div><span>01</span><strong>React showcase</strong><p>Professional reviewer-facing interface served from /.</p></div>
            <div><span>02</span><strong>FastAPI backend</strong><p>Health, benchmark, analyze, compress, and triage endpoints.</p></div>
            <div><span>03</span><strong>CI evidence</strong><p>React build, Render entrypoint check, Docker build, benchmark checks.</p></div>
          </div>
        </article>

        <article className="card">
          <div className="section-heading compact">
            <p className="eyebrow">Safety posture</p>
            <h2>Review-safe</h2>
          </div>
          <ul className="evidence-list">
            {evidence.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </article>

        <article className="card span-3">
          <div className="section-heading">
            <p className="eyebrow">Use cases</p>
            <h2>Industrial scenarios</h2>
          </div>
          <div className="scenario-grid">
            {scenarios.map((scenario) => (
              <div className="scenario" key={scenario.title}>
                <span>{scenario.metric}</span>
                <h3>{scenario.title}</h3>
                <p>{scenario.body}</p>
              </div>
            ))}
          </div>
        </article>

        <section id="demo" className="workbench span-3">
          <div className="workbench-header">
            <div>
              <p className="eyebrow">Live synthetic workbench</p>
              <h2>Document analysis</h2>
            </div>
            <div className={`run-state ${status}`}>{status}</div>
          </div>

          <div className="workbench-grid">
            <div className="input-panel">
              <label htmlFor="payload">Synthetic document</label>
              <textarea id="payload" value={text} onChange={(event) => setText(event.target.value)} />
              <div className="form-row">
                <label htmlFor="source">Source</label>
                <input id="source" value={source} onChange={(event) => setSource(event.target.value)} />
              </div>
              <div className="input-meta">
                <span>{tokenEstimate} estimated tokens</span>
                <button onClick={() => setText(DEFAULT_TEXT)}>Reset sample</button>
              </div>
              <button className="primary-action" onClick={analyze} disabled={status === 'loading'}>
                {status === 'loading' ? 'Running analysis…' : 'Analyze synthetic document'}
              </button>
            </div>

            <div className="output-panel">
              <div className="output-title">
                <span>API result</span>
                <small>POST /analyze</small>
              </div>
              <ResultPanel status={status} result={result} error={error} />
            </div>
          </div>
        </section>

        <article className="card span-3">
          <div className="section-heading">
            <p className="eyebrow">API surface</p>
            <h2>Operational endpoints</h2>
          </div>
          <div className="api-grid">
            {apiCards.map((card) => (
              <a className={`api-card ${card.tone}`} href={card.path} key={card.path}>
                <span>{card.method}</span>
                <strong>{card.label}</strong>
                <code>{card.path}</code>
              </a>
            ))}
          </div>
        </article>
      </section>
    </main>
  )
}
