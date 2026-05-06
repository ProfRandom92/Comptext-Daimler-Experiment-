import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

const NODES = [
  {
    id: 'input',
    icon: '📄',
    label: 'Rohdokument',
    sub: 'Wartungsprotokoll · OBD · QA · SAP',
    color: '#8899AA',
    bg: '#1a2233',
  },
  {
    id: 'intake',
    icon: '🔒',
    label: 'IntakeAgent',
    sub: 'DSGVO-Sanitisierung + KVTC-Kompression',
    color: '#00A0DC',
    bg: '#0D1F33',
    badge: 'Layer 1',
  },
  {
    id: 'triage',
    icon: '🔎',
    label: 'TriageAgent',
    sub: 'P1/P2/P3 · Regex + 70+ OBD-Codes',
    color: '#F57C00',
    bg: '#1F150A',
    badge: 'Layer 2',
  },
  {
    id: 'analysis',
    icon: '🤖',
    label: 'AnalysisAgent',
    sub: 'LLM-Inferenz + MD5-LRU-Cache',
    color: '#00C853',
    bg: '#0A1F10',
    badge: 'Layer 3',
  },
  {
    id: 'output',
    icon: '📊',
    label: 'Ergebnis',
    sub: 'Dashboard · FastAPI · JSON/CSV',
    color: '#8899AA',
    bg: '#1a2233',
  },
]

function Packet({ delay, color }) {
  return (
    <motion.div
      className="absolute left-1/2 -translate-x-1/2 w-3 h-3 rounded-full z-10"
      style={{ background: color, boxShadow: `0 0 10px ${color}` }}
      initial={{ top: '0%', opacity: 0 }}
      animate={{ top: ['0%', '100%'], opacity: [0, 1, 1, 0] }}
      transition={{ duration: 1.6, delay, repeat: Infinity, repeatDelay: 0.4, ease: 'linear' }}
    />
  )
}

function Connector({ color, packets = 2 }) {
  return (
    <div className="relative flex flex-col items-center" style={{ height: 64 }}>
      {/* Line */}
      <div
        className="absolute top-0 bottom-0 w-[2px] left-1/2 -translate-x-1/2"
        style={{ background: `linear-gradient(to bottom, ${color}44, ${color}88, ${color}44)` }}
      />
      {/* Arrow */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-0"
        style={{
          borderLeft: '5px solid transparent',
          borderRight: '5px solid transparent',
          borderTop: `7px solid ${color}`,
        }}
      />
      {/* Packets */}
      {Array.from({ length: packets }, (_, i) => (
        <Packet key={i} delay={i * 0.8} color={color} />
      ))}
    </div>
  )
}

export default function ArchitectureSlide() {
  const connectorColors = ['#00A0DC', '#F57C00', '#00C853', '#8899AA']

  return (
    <div className="w-full h-full flex flex-col justify-center px-12 py-10 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-2">03 / Architektur</div>
        <h2 className="text-4xl font-black">
          3-Agent <span className="text-gradient">Pipeline</span>
        </h2>
        <p className="text-[#8899AA] mt-1">
          Dokument → IntakeAgent → TriageAgent → AnalysisAgent → Ergebnis
        </p>
      </motion.div>

      <div className="flex gap-8 items-start">
        {/* Left: Pipeline */}
        <div className="flex flex-col items-center flex-shrink-0 w-72">
          {NODES.map((node, i) => (
            <div key={node.id} className="flex flex-col items-center w-full">
              <motion.div
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.12, duration: 0.4, ease: 'backOut' }}
                className="w-full rounded-xl border px-4 py-3 relative"
                style={{
                  background: node.bg,
                  borderColor: `${node.color}44`,
                  boxShadow: `0 0 20px ${node.color}11`,
                }}
              >
                {node.badge && (
                  <span
                    className="absolute -top-2.5 right-3 text-[10px] font-mono px-2 py-0.5 rounded-full"
                    style={{ background: `${node.color}22`, color: node.color, border: `1px solid ${node.color}44` }}
                  >
                    {node.badge}
                  </span>
                )}
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{node.icon}</span>
                  <div>
                    <div className="font-bold text-sm" style={{ color: node.color }}>{node.label}</div>
                    <div className="text-[11px] text-[#6677AA] leading-tight">{node.sub}</div>
                  </div>
                </div>
              </motion.div>

              {i < NODES.length - 1 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 + i * 0.12 }}
                  className="w-full flex justify-center"
                >
                  <Connector color={connectorColors[i]} />
                </motion.div>
              )}
            </div>
          ))}
        </div>

        {/* Right: Details */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
          className="flex-1 space-y-4"
        >
          {/* IntakeAgent detail */}
          <div className="card p-4" style={{ borderColor: 'rgba(0,160,220,0.3)' }}>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-[#00A0DC] text-lg">🔒</span>
              <span className="font-bold text-[#00A0DC] text-sm">IntakeAgent – Layer 1</span>
            </div>
            <div className="space-y-1.5">
              {[
                ['FIN-Maskierung', 'WDB906232N3123456 → FIN_***123456'],
                ['Personal-Hash', 'P12345 → PERS_A1B2C3D4 (MD5)'],
                ['E-Mail entfernt', 'max@daimler.com → [EMAIL_ENTFERNT]'],
                ['KVTC-Kompression', '1847 Tokens → 187 Tokens (−88%)'],
              ].map(([k, v]) => (
                <div key={k} className="flex gap-2 text-xs font-mono">
                  <span className="text-[#445566] w-36 flex-shrink-0">{k}</span>
                  <span className="text-[#8899AA]">{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* TriageAgent detail */}
          <div className="card p-4" style={{ borderColor: 'rgba(245,124,0,0.3)' }}>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">🔎</span>
              <span className="font-bold text-[#F57C00] text-sm">TriageAgent – Layer 2</span>
            </div>
            <div className="flex gap-3">
              {[
                { label: 'P1_KRITISCH', color: '#E40520', codes: 'P0300, U0073, C0110, B0001' },
                { label: 'P2_DRINGEND', color: '#F57C00', codes: 'P0171, P0420, P0700, P229F' },
                { label: 'P3_ROUTINE', color: '#00C853', codes: 'P0030, P1000, U0184' },
              ].map((p) => (
                <div key={p.label} className="flex-1 rounded-lg p-2.5" style={{ background: `${p.color}11`, border: `1px solid ${p.color}33` }}>
                  <div className="text-[11px] font-bold mb-1" style={{ color: p.color }}>{p.label}</div>
                  <div className="text-[10px] text-[#6677AA] font-mono leading-relaxed">{p.codes}</div>
                </div>
              ))}
            </div>
          </div>

          {/* AnalysisAgent detail */}
          <div className="card p-4" style={{ borderColor: 'rgba(0,200,83,0.3)' }}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🤖</span>
              <span className="font-bold text-[#00C853] text-sm">AnalysisAgent – Layer 3</span>
            </div>
            <div className="flex gap-2 text-xs">
              {[
                { label: '🧪 Mock', sub: 'Test/Demo', color: '#8899AA' },
                { label: '🏠 Gemma 2B', sub: 'Air-Gap', color: '#A78BFA' },
                { label: '☁️ Claude Haiku', sub: 'Cloud', color: '#00A0DC' },
              ].map((b) => (
                <div key={b.label} className="flex-1 text-center rounded-lg py-2 px-1"
                  style={{ background: `${b.color}11`, border: `1px solid ${b.color}33` }}>
                  <div className="font-semibold" style={{ color: b.color }}>{b.label}</div>
                  <div className="text-[10px] text-[#6677AA]">{b.sub}</div>
                </div>
              ))}
            </div>
            <div className="mt-2 text-[11px] text-[#445566] font-mono">
              💾 LRU-Cache 256 Slots · Hit-Rate ~40% · Thread-safe ✓
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
