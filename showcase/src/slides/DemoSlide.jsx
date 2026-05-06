import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// OBD codes mirrored from src/core/obd_database.py
const OBD_DB = {
  P0300: { desc: 'Zündaussetzer erkannt (zufällig)', prio: 'P1_KRITISCH', system: 'Motor' },
  P0301: { desc: 'Zündaussetzer Zylinder 1', prio: 'P1_KRITISCH', system: 'Motor' },
  P0302: { desc: 'Zündaussetzer Zylinder 2', prio: 'P1_KRITISCH', system: 'Motor' },
  P0303: { desc: 'Zündaussetzer Zylinder 3', prio: 'P1_KRITISCH', system: 'Motor' },
  P0304: { desc: 'Zündaussetzer Zylinder 4', prio: 'P1_KRITISCH', system: 'Motor' },
  P0524: { desc: 'Öldruck zu niedrig – kritisch', prio: 'P1_KRITISCH', system: 'Motor' },
  U0073: { desc: 'CAN-Bus Kommunikationsverlust', prio: 'P1_KRITISCH', system: 'Netzwerk' },
  U0100: { desc: 'Kommunikationsverlust ECM/PCM', prio: 'P1_KRITISCH', system: 'Netzwerk' },
  C0110: { desc: 'Bremsventil-Motorstörung', prio: 'P1_KRITISCH', system: 'Bremse' },
  B0001: { desc: 'Fahrer-Airbag-Zündkreis', prio: 'P1_KRITISCH', system: 'Airbag' },
  P0171: { desc: 'Gemisch zu mager (Bank 1)', prio: 'P2_DRINGEND', system: 'Motor' },
  P0172: { desc: 'Gemisch zu fett (Bank 1)', prio: 'P2_DRINGEND', system: 'Motor' },
  P0420: { desc: 'Katalysator-Effizienz zu niedrig', prio: 'P2_DRINGEND', system: 'Abgas' },
  P0700: { desc: 'Getriebesteuerungsfehler', prio: 'P2_DRINGEND', system: 'Getriebe' },
  P229F: { desc: 'AdBlue-Konzentration zu niedrig', prio: 'P2_DRINGEND', system: 'SCR/AdBlue' },
  P20EE: { desc: 'SCR-NOx-Katalysator Effizienz', prio: 'P2_DRINGEND', system: 'SCR/AdBlue' },
  P0030: { desc: 'Lambdasonde Heizkreis (B1S1)', prio: 'P3_ROUTINE', system: 'Abgas' },
  P1000: { desc: 'OBD-Systemprüfung unvollständig', prio: 'P3_ROUTINE', system: 'OBD' },
  U0184: { desc: 'Kommunikationsverlust Radio', prio: 'P3_ROUTINE', system: 'Comfort' },
}

const PRIO_CONFIG = {
  P1_KRITISCH: { color: '#E40520', bg: '#E4052015', label: '🔴 P1 – KRITISCH', action: 'Sofortige Eskalation' },
  P2_DRINGEND: { color: '#F57C00', bg: '#F57C0015', label: '🟠 P2 – DRINGEND', action: 'Einplanung 24h' },
  P3_ROUTINE:  { color: '#00C853', bg: '#00C85315', label: '🟢 P3 – ROUTINE', action: 'Nächste Inspektion' },
  UNBEKANNT:   { color: '#8899AA', bg: '#88990015', label: '⚪ UNBEKANNT', action: 'Manuelle Prüfung' },
}

// DSGVO demo
function applyDsgvo(text) {
  return text
    .replace(/\b(WDB|VIN|FIN)[A-Z0-9]{14,}\b/gi, 'FIN_***XXXXXX')
    .replace(/\bP\d{4,6}\b/g, m => `PERS_${m.slice(1).padStart(8, '0').slice(0,8).toUpperCase()}`)
    .replace(/[\w.-]+@[\w.-]+\.\w+/g, '[EMAIL_ENTFERNT]')
    .replace(/(\+49|0049|0)[- \/]?[\d \-\/]{8,}/g, '[TEL_ENTFERNT]')
}

const EXAMPLE_INPUTS = [
  { label: 'P0300', input: 'P0300' },
  { label: 'U0100', input: 'U0100' },
  { label: 'P0420', input: 'P0420' },
  { label: 'P1000', input: 'P1000' },
  { label: 'FIN + P0524', input: 'FIN: WDB906232N3123456\nFehler: P0524 Öldruck kritisch\nTel: +49 711 1234' },
]

export default function DemoSlide() {
  const [input, setInput] = useState('')
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('obd')

  const classify = useCallback((text) => {
    const upper = text.toUpperCase()
    const codePattern = /[PBCU][0-9A-F]{4}/g
    const found = [...upper.matchAll(codePattern)].map(m => m[0])

    let topPrio = null
    const details = []

    for (const code of found) {
      const info = OBD_DB[code]
      if (info) {
        details.push({ code, ...info })
        if (!topPrio || (info.prio === 'P1_KRITISCH') ||
            (info.prio === 'P2_DRINGEND' && topPrio !== 'P1_KRITISCH'))
          topPrio = info.prio
      } else if (found.length > 0) {
        details.push({ code, desc: 'Unbekannter Code', prio: 'UNBEKANNT', system: '—' })
        if (!topPrio) topPrio = 'UNBEKANNT'
      }
    }

    const sanitized = applyDsgvo(text)
    setResult({ topPrio: topPrio || 'UNBEKANNT', details, sanitized, codes: found })
  }, [])

  const handleInput = (val) => {
    setInput(val)
    if (val.trim()) {
      classify(val)
    } else {
      setResult(null)
    }
  }

  const cfg = result ? PRIO_CONFIG[result.topPrio] : null

  return (
    <div className="w-full h-full flex flex-col justify-center px-12 py-8 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-5">
        <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-2">07 / Live Demo</div>
        <h2 className="text-4xl font-black">
          Interaktive <span className="text-gradient">Demo</span>
        </h2>
        <p className="text-[#8899AA] mt-1">OBD-Code eingeben oder Schnellbeispiel wählen</p>
      </motion.div>

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Input */}
        <div className="flex flex-col gap-4">
          {/* Quick examples */}
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_INPUTS.map((ex) => (
              <button
                key={ex.label}
                onClick={() => handleInput(ex.input)}
                className="text-xs font-mono px-3 py-1.5 rounded-full border transition-all hover:scale-105"
                style={{
                  borderColor: 'rgba(0,160,220,0.35)',
                  background: input === ex.input ? 'rgba(0,160,220,0.15)' : 'rgba(0,160,220,0.05)',
                  color: input === ex.input ? '#00A0DC' : '#8899AA',
                }}
              >
                {ex.label}
              </button>
            ))}
          </div>

          {/* Text area */}
          <textarea
            value={input}
            onChange={(e) => handleInput(e.target.value)}
            placeholder={'OBD-Code eingeben, z.B. P0300\n\nOder mehrere Codes:\nP0300 U0073 C0110\n\nOder mit PII:\nFIN: WDB906232N3123456\nFehler: P0524'}
            className="flex-1 min-h-[160px] bg-[#0D1526] border border-[rgba(0,160,220,0.2)] rounded-xl p-4 text-sm font-mono text-[#B0C4D8] resize-none focus:outline-none focus:border-[#00A0DC] placeholder-[#2A3A4A] transition-colors"
          />

          {/* Hint */}
          <div className="text-[11px] font-mono text-[#334455]">
            ↑ OBD-Codes: P0300, U0073, C0110, P229F, P1000 …
          </div>
        </div>

        {/* Right: Result */}
        <div className="flex flex-col gap-3">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key={result.topPrio + result.codes.join()}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="flex flex-col gap-3"
              >
                {/* Priority badge */}
                <div
                  className="rounded-xl p-4 text-center"
                  style={{ background: cfg.bg, border: `1px solid ${cfg.color}44` }}
                >
                  <div className="text-2xl font-black" style={{ color: cfg.color }}>
                    {cfg.label}
                  </div>
                  <div className="text-sm text-[#8899AA] mt-1">{cfg.action}</div>
                </div>

                {/* Code details */}
                {result.details.length > 0 && (
                  <div className="card p-3">
                    <div className="text-[10px] font-mono text-[#445566] uppercase tracking-widest mb-2">
                      Erkannte OBD-Codes ({result.details.length})
                    </div>
                    <div className="space-y-1.5">
                      {result.details.map((d) => {
                        const dc = PRIO_CONFIG[d.prio]
                        return (
                          <div key={d.code} className="flex items-start gap-2 text-xs font-mono">
                            <span className="font-bold w-14 flex-shrink-0" style={{ color: dc.color }}>{d.code}</span>
                            <span className="text-[#6677AA] flex-1">{d.desc}</span>
                            <span className="text-[10px] text-[#445566]">{d.system}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* DSGVO sanitized output (if PII detected) */}
                {result.sanitized !== input && (
                  <div className="card p-3">
                    <div className="text-[10px] font-mono text-[#00A0DC] uppercase tracking-widest mb-2">
                      DSGVO-sanitisiert (geht an LLM)
                    </div>
                    <pre className="text-[11px] font-mono text-[#6677AA] whitespace-pre-wrap leading-relaxed">
                      {result.sanitized}
                    </pre>
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center h-full text-center py-12"
              >
                <div className="text-4xl mb-3 opacity-30">🔎</div>
                <div className="text-sm text-[#334455] font-mono">
                  OBD-Code eingeben um die<br />Live-Klassifikation zu sehen
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Stack info */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="card p-3 mt-auto"
          >
            <div className="text-[10px] font-mono text-[#445566] uppercase tracking-widest mb-2">Tech-Stack</div>
            <div className="flex flex-wrap gap-1.5">
              {['Python 3.11', 'FastAPI', 'Streamlit', 'Anthropic Claude', 'Ollama Gemma 2B', 'Docker', 'pytest · 62 Tests'].map((t) => (
                <span key={t} className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#0D1526] text-[#556677] border border-[rgba(0,160,220,0.12)]">
                  {t}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
