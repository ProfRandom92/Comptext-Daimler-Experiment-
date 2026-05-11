import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const apiUrl = (path) => `${API_BASE_URL}${path}`

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
  'Vercel can serve the static showcase separately from the API',
  'Render entrypoint and Docker image remain available as API backend',
]

const criticChecks = [
  { label: 'Corpus integrity', value: 'versioned', detail: 'scenario mix, fixture count, hash, synthetic-only boundary' },
  { label: 'Repeatability', value: 'replayable', detail: 'commit SHA, runner version, environment notes, CI command trail' },
  { label: 'Distribution', value: 'p50/p95/p99', detail: 'sample count, warmups, variance, weak-case exposure' },
  { label: 'Quality gate', value: 'not just %', detail: 'token reduction plus semantic retention proxy and family coverage' },
]

const benchmarkRows = [
  { case: 'repetitive_xentry_2k', reduction: '99.59%', coverage: '100.00%', p95: '1.12s', decision: 'pass', caveat: 'Best-case repeated families; strong value but not sufficient alone.' },
  { case: 'mixed_obd_workshop_1_5k', reduction: '98.88%', coverage: '100.00%', p95: '0.61s', decision: 'pass', caveat: 'Realistic structured middle case; keep replay checks attached.' },
  { case: 'high_entropy_json_750', reduction: '99.46%', coverage: '1.60%', p95: '0.54s', decision: 'warn', caveat: 'Compression is misleading here; low family coverage must be visible.' },
  { case: 'short_sparse_3', reduction: '65.22%', coverage: '100.00%', p95: '0.002s', decision: 'pass', caveat: 'Micro-frame avoids overhead dominating tiny inputs.' },
]

const qualityGates = [
  { name: 'Synthetic-only sanitizer', state: 'pass', note: 'No raw production logs, secrets, tokens, cookies, or customer payloads.' },
  { name: 'Regression policy', state: 'warn', note: 'Fail only on clear regressions with baseline; otherwise show insufficient baseline.' },
  { name: 'Weak-case transparency', state: 'pass', note: 'High-entropy case remains visible and explicitly caveated.' },
  { name: 'Artifact traceability', state: 'pass', note: 'Reports and docs remain diffable under docs/reports and docs/*.md.' },
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

function ResultPanel({ result, error }) {
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

function DecisionBadge({ value }) {
  return <span className={`decision-badge ${value}`}>{value}</span>
}

function BenchmarkEvidenceCenter() {
  return (
    <section id="benchmark-evidence" className="evidence-center span-3">
      <div className="evidence-hero">
        <div>
          <p className="eyebrow">Benchmark evidence center</p>
          <h2>Built for hostile review, not marketing screenshots.</h2>
          <p>
            The dashboard separates compression claims from repeatability, corpus integrity,
            weak-case visibility, and regression policy. A critic should be able to reproduce
            the run, inspect the caveats, and understand what the numbers do not prove.
          </p>
        </div>
        <div className="evidence-score">
          <span>review posture</span>
          <strong>HOLD-READY</strong>
          <small>Promote only with current artifacts and visible caveats.</small>
        </div>
      </div>

      <div className="critic-grid">
        {criticChecks.map((check) => (
          <article className="critic-card" key={check.label}>
            <span>{check.label}</span>
            <strong>{check.value}</strong>
            <p>{check.detail}</p>
          </article>
        ))}
      </div>

      <div className="benchmark-table-wrap">
        <div className="table-title">
          <div>
            <p className="eyebrow">Distribution and caveat table</p>
            <h3>Representative benchmark cases</h3>
          </div>
          <a href={apiUrl('/benchmark')}>Open live /benchmark</a>
        </div>
        <div className="benchmark-table">
          <div className="benchmark-row benchmark-head">
            <span>Case</span><span>Reduction</span><span>Coverage</span><span>p95</span><span>Decision</span><span>Caveat</span>
          </div>
          {benchmarkRows.map((row) => (
            <div className="benchmark-row" key={row.case}>
              <strong>{row.case}</strong>
              <span>{row.reduction}</span>
              <span>{row.coverage}</span>
              <span>{row.p95}</span>
              <DecisionBadge value={row.decision} />
              <p>{row.caveat}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="gate-grid">
        {qualityGates.map((gate) => (
          <article className="gate-card" key={gate.name}>
            <DecisionBadge value={gate.state} />
            <h3>{gate.name}</h3>
            <p>{gate.note}</p>
          </article>
        ))}
      </div>
    </section>
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
      const response = await fetch(apiUrl('/analyze'), {
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
            <a href="#benchmark-evidence">Evidence</a>
            <a href={apiUrl('/health')}>Health</a>
            <a href={apiUrl('/docs')}>API Docs</a>
            <a href={apiUrl('/benchmark')}>Benchmark</a>
          </div>
        </nav>

        <div className="hero-grid">
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
            <p className="eyebrow">Vercel-ready industrial AI dashboard</p>
            <h1>Token compression, triage, and safe diagnostic replay.</h1>
            <p className="hero-copy">
              A polished synthetic showcase for CompText/KVTC workflows: critic-facing benchmark evidence,
              React frontend, API integration, regression gates, and no real Daimler payloads.
            </p>
            <div className="hero-actions">
              <button onClick={analyze} disabled={status === 'loading'}>{status === 'loading' ? 'Analyzing…' : 'Run synthetic demo'}</button>
              <a href="#benchmark-evidence">Review evidence</a>
              <a href="#demo">Open workbench</a>
            </div>
          </motion.div>

          <motion.aside className="signal-card" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.45, delay: 0.08 }}>
            <span className="status-pill">Showcase deployment</span>
            <div className="signal-metric">94%</div>
            <p>Target compression posture for structured synthetic diagnostics.</p>
            <div className="signal-grid">
              <span>Frontend</span><strong>Vercel</strong>
              <span>API</span><strong>Configurable</strong>
              <span>Data</span><strong>synthetic</strong>
            </div>
          </motion.aside>
        </div>
      </section>

      <section className="content-grid">
        <BenchmarkEvidenceCenter />

        <article className="card span-2">
          <div className="section-heading">
            <p className="eyebrow">System overview</p>
            <h2>One dashboard, API backend optional</h2>
          </div>
          <div className="pipeline">
            <div><span>01</span><strong>Vercel showcase</strong><p>Professional reviewer-facing static frontend served from the edge.</p></div>
            <div><span>02</span><strong>FastAPI backend</strong><p>Health, benchmark, analyze, compress, and triage endpoints via configurable API base URL.</p></div>
            <div><span>03</span><strong>CI evidence</strong><p>React build, Render entrypoint check, Docker build, benchmark checks, live smoke checks.</p></div>
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
                <small>POST {apiUrl('/analyze')}</small>
              </div>
              <ResultPanel result={result} error={error} />
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
              <a className={`api-card ${card.tone}`} href={apiUrl(card.path)} key={card.path}>
                <span>{card.method}</span>
                <strong>{card.label}</strong>
                <code>{apiUrl(card.path)}</code>
              </a>
            ))}
          </div>
        </article>
      </section>
    </main>
  )
}
