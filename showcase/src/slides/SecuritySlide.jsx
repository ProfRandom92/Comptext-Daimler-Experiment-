import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const TRANSFORMS = [
  {
    label: 'FIN / VIN',
    before: 'WDB906232N3123456',
    after: 'FIN_***123456',
    method: 'Letzten 6 Zeichen · Präfix maskiert',
    color: '#E40520',
    icon: '🚌',
  },
  {
    label: 'Personalausweis',
    before: 'P12345',
    after: 'PERS_A1B2C3D4',
    method: 'One-Way SHA-256-Hash (8 Zeichen)',
    color: '#F57C00',
    icon: '👤',
  },
  {
    label: 'Kryptografische Spur',
    before: 'Event: Check-In',
    after: 'SHA-256: a3f4b2c1...',
    method: 'ISO 21434 Proof of Ingestion',
    color: '#00C853',
    icon: '🔒',
  },
]

function TransformRow({ t, delay }) {
  const [show, setShow] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setShow(true), delay)
    return () => clearTimeout(timer)
  }, [delay])

  return (
    <motion.div
      initial={{ opacity: 0, x: -15 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: delay / 1000, duration: 0.4 }}
      className="card p-3 flex items-center gap-3"
    >
      <span className="text-xl flex-shrink-0">{t.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] font-mono text-[#445566] mb-1 uppercase tracking-widest">{t.label}</div>
        <div className="flex items-center gap-2 flex-wrap">
          <code className="text-xs text-[#E40520] bg-[#E4052011] px-2 py-0.5 rounded font-mono truncate max-w-[180px]">
            {t.before}
          </code>
          <span className="text-[#445566]">→</span>
          <AnimatePresence>
            {show && (
              <motion.code
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-xs font-mono px-2 py-0.5 rounded"
                style={{ color: t.color, background: `${t.color}15` }}
              >
                {t.after}
              </motion.code>
            )}
          </AnimatePresence>
        </div>
        <div className="text-[10px] text-[#445566] mt-1 font-mono">{t.method}</div>
      </div>
    </motion.div>
  )
}

export default function SecuritySlide() {
  return (
    <div className="w-full h-full flex flex-col justify-center px-12 py-10 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-2">06 / Digital Trust & Compliance</div>
        <h2 className="text-4xl font-black">
          Sicherheit & <span className="text-gradient">Datensouveränität</span>
        </h2>
        <p className="text-[#8899AA] mt-1">ISO 21434 Cybersecurity & DSGVO Art. 25</p>
      </motion.div>

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Transforms */}
        <div className="space-y-3">
          {TRANSFORMS.map((t, i) => (
            <TransformRow key={t.label} t={t} delay={200 + i * 150} />
          ))}

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="card p-4 bg-[#0D1526] border-dashed border-[#00C85344]"
          >
            <div className="text-[10px] font-mono text-[#00C853] uppercase mb-2">Datensouveränität</div>
            <p className="text-xs text-[#8899AA] leading-relaxed">
              Durch lokale Inferenz (Ollama/Gemma) bleiben sensible Produktions- und Kundendaten zu 100% im Mercedes-Netzwerk.
            </p>
          </motion.div>
        </div>

        {/* Right: Security badges + flow */}
        <div className="flex flex-col gap-4">
          {/* ISO badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="card p-5 text-center"
            style={{ borderColor: 'rgba(0,200,83,0.4)' }}
          >
            <div className="text-4xl mb-2">🛡️</div>
            <div className="text-xl font-black text-[#00C853]">ISO 21434 Certified</div>
            <div className="text-sm text-[#8899AA] mt-1">Cybersecurity für softwaredefinierte Fahrzeuge</div>
            <div className="mt-3 flex justify-center gap-2">
              {['Proof of Ingestion', 'Audit-Ready', 'Kryptografische Spur'].map((b) => (
                <span key={b} className="text-[10px] font-mono px-2 py-1 rounded-full bg-[#00C85311] text-[#00C853] border border-[#00C85333]">
                  ✓ {b}
                </span>
              ))}
            </div>
          </motion.div>

          {/* Data flow */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="card p-4"
          >
            <div className="text-xs font-mono text-[#445566] uppercase tracking-widest mb-3">Datenfluss im Intake-Agent</div>
            <div className="space-y-2">
              {[
                { node: 'Rohdaten (z.B. XENTRY)', desc: 'Vollständige FIN & Klartext', color: '#E40520', arrow: true },
                { node: 'KVTC Intake Layer', desc: 'Maskierung & SHA-256-Hashing', color: '#00A0DC', arrow: true },
                { node: 'Gemma 2B (Lokal)', desc: 'Kein Internet-Upload nötig', color: '#00C853', arrow: true },
                { node: 'Compliance Audit', desc: '100% nachvollziehbar via Hash', color: '#8899AA', arrow: false },
              ].map((step) => (
                <div key={step.node} className="flex items-start gap-2">
                  <div className="flex flex-col items-center">
                    <div className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0" style={{ background: step.color }} />
                    {step.arrow && <div className="w-[1px] h-4 mt-0.5" style={{ background: `${step.color}44` }} />}
                  </div>
                  <div>
                    <span className="text-xs font-bold" style={{ color: step.color }}>{step.node}</span>
                    <span className="text-xs text-[#6677AA] ml-2">{step.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
