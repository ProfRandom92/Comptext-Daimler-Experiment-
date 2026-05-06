import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const RAW_LINES = [
  'Fahrzeugidentifikation: WDB906232N3123456',
  'Personalausweis: P12345 – Meister Müller',
  'Datum: 14.03.2026 · Lfd.-Nr: SAP-88221-A',
  'Fehlercodes: P0300 P0301 P0302 P0303',
  'Kilometerstand: 183.421 km',
  'Motor: OM936 Euro6d, 290 PS, 1.200 Nm',
  'Zylinder 1-4: Zündaussetzer erkannt',
  'Kraftstoff: 98% Diesel · AdBlue: 22%',
  'Kühlmitteltemperatur: 94°C (Grenzwert 95°C)',
  'Letzte Inspektion: 170.000 km (aktuell: −13km)',
  'Empfehlung: Sofortige Werkstattaufnahme nötig',
  'Freigabe-Code: AUTH-BUS-2026-0314-KRITISCH',
]

const KVTC_FRAME = [
  { k: 'K:', v: 'FIN, PERS, SAP_NR, KM, TEMP, OBD' },
  { k: 'V:', v: 'FIN_***123456, PERS_A1B2C3D4, SAP-88221-A, 183421, 94, P0300..P0303' },
  { k: 'T:', v: 'VIN, HASH, SAP_ID, NUMERIC, CELSIUS, OBD_MULTI' },
  { k: 'C:', v: 'P0300·P1·KRITISCH, OM936·290PS, KUEHL·94°C, KM·183421' },
  { k: '✓:', v: 'MD5:a3f4b2c1  |  Tokens: 187  |  Ratio: 88%' },
]

function Counter({ from, to, suffix = '', delay = 0 }) {
  const [val, setVal] = useState(from)
  useEffect(() => {
    let start
    const dur = 1200
    const raf = (ts) => {
      if (!start) start = ts
      const p = Math.min((ts - start) / dur, 1)
      setVal(Math.round(from + (to - from) * p))
      if (p < 1) requestAnimationFrame(raf)
    }
    const t = setTimeout(() => requestAnimationFrame(raf), delay)
    return () => clearTimeout(t)
  }, [from, to, delay])
  return <>{val}{suffix}</>
}

export default function KVTCSlide() {
  const [phase, setPhase] = useState(0)
  // phase 0 = raw, 1 = compressing, 2 = done

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 800)
    const t2 = setTimeout(() => setPhase(2), 2400)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [])

  return (
    <div className="w-full h-full flex flex-col justify-center px-12 py-10 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-2">04 / KVTC-Algorithmus</div>
        <h2 className="text-4xl font-black">
          4-Layer <span className="text-gradient">Sandwich-Kompression</span>
        </h2>
        <p className="text-[#8899AA] mt-1">
          Key–Value–Type–Context Frame · ~88% Token-Reduktion
        </p>
      </motion.div>

      <div className="grid grid-cols-2 gap-6 flex-1 min-h-0">
        {/* Left: Raw document */}
        <div className="card p-4 flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs font-mono text-[#8899AA] uppercase tracking-widest">Rohdokument</div>
            <div className="text-xs font-mono text-[#E40520]">
              <Counter from={0} to={1847} delay={200} /> Tokens
            </div>
          </div>
          <div className="flex-1 overflow-hidden space-y-1">
            {RAW_LINES.map((line, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 1 }}
                animate={phase >= 1 ? {
                  opacity: [1, 0.2],
                  scaleY: [1, 0],
                  height: [24, 0],
                } : { opacity: 1 }}
                transition={{ delay: phase >= 1 ? i * 0.08 : 0, duration: 0.3 }}
                className="text-xs font-mono text-[#6677AA] whitespace-nowrap overflow-hidden leading-6"
                style={{ height: 24, transformOrigin: 'top' }}
              >
                <span className="text-[#2A3A4A] mr-2">{String(i + 1).padStart(2, '0')}</span>
                {line}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Right: KVTC output */}
        <div className="flex flex-col gap-4">
          <div className="card p-4 flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-mono text-[#00A0DC] uppercase tracking-widest">KVTC-Frame</div>
              <AnimatePresence>
                {phase >= 2 && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-xs font-mono text-[#00C853]"
                  >
                    <Counter from={1847} to={187} delay={0} /> Tokens
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="flex-1 space-y-2">
              {KVTC_FRAME.map((row, i) => (
                <AnimatePresence key={row.k}>
                  {phase >= 2 && (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.12 }}
                      className="flex gap-3 text-xs font-mono"
                    >
                      <span
                        className="flex-shrink-0 font-bold w-6"
                        style={{ color: row.k === '✓:' ? '#00C853' : '#00A0DC' }}
                      >
                        {row.k}
                      </span>
                      <span className="text-[#8899AA] break-all leading-relaxed">{row.v}</span>
                    </motion.div>
                  )}
                </AnimatePresence>
              ))}
            </div>
          </div>

          {/* Reduction stats */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Token-Reduktion', val: 88, suffix: '%', color: '#00C853' },
              { label: 'Byte-Reduktion', val: 90, suffix: '%', color: '#00A0DC' },
              { label: 'Latenz KVTC', val: 12, suffix: 'ms', color: '#F57C00' },
            ].map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, y: 20 }}
                animate={phase >= 2 ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.1 + 0.5 }}
                className="card p-3 text-center"
              >
                <div className="text-2xl font-black" style={{ color: s.color }}>
                  {phase >= 2 ? <Counter from={0} to={s.val} suffix={s.suffix} delay={i * 100} /> : '—'}
                </div>
                <div className="text-[10px] text-[#556677] mt-1">{s.label}</div>
              </motion.div>
            ))}
          </div>

          {/* Sandwich zones legend */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
            className="card p-3"
          >
            <div className="text-[10px] font-mono text-[#445566] uppercase tracking-widest mb-2">Sandwich-Zonen</div>
            <div className="flex gap-2">
              {[
                { zone: 'Header', desc: 'Lossless · SOPs · Stammdaten', color: '#00A0DC' },
                { zone: 'Middle', desc: 'Aggressiv · Top 25% Dichte', color: '#F57C00' },
                { zone: 'Window', desc: 'Lossless · Aktuelle Diagnose', color: '#00C853' },
              ].map((z) => (
                <div key={z.zone} className="flex-1 rounded-lg px-2 py-1.5" style={{ background: `${z.color}11`, border: `1px solid ${z.color}33` }}>
                  <div className="text-[10px] font-bold" style={{ color: z.color }}>{z.zone}</div>
                  <div className="text-[9px] text-[#556677] leading-tight">{z.desc}</div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
