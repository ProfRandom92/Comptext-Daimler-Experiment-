import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

function useCountUp(target, duration = 1500, delay = 0) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    const t = setTimeout(() => {
      let start
      const tick = (ts) => {
        if (!start) start = ts
        const p = Math.min((ts - start) / duration, 1)
        setVal(Math.round(target * p))
        if (p < 1) requestAnimationFrame(tick)
      }
      requestAnimationFrame(tick)
    }, delay)
    return () => clearTimeout(t)
  }, [target, duration, delay])
  return val
}

const BIG_METRICS = [
  { value: 88, suffix: '%', label: 'Token-Reduktion', sub: 'Ø über alle Dokumenttypen', color: '#00C853', icon: '📦' },
  { value: 62, suffix: '', label: 'Tests bestanden', sub: '0 Fehler · ~0.5s Laufzeit', color: '#00A0DC', icon: '✅' },
  { value: 70, suffix: '+', label: 'OBD-Codes', sub: 'SAE J2012 · ISO 14229', color: '#F57C00', icon: '🔧' },
  { value: 1, suffix: 'ms', label: 'Cache-Hit', sub: 'LRU 256 Slots · Thread-safe', color: '#8B5CF6', icon: '⚡' },
]

const LATENCY = [
  { label: 'Cache-Hit', p50: 1, p95: 2, color: '#00C853' },
  { label: 'Triage', p50: 8, p95: 12, color: '#00A0DC' },
  { label: 'KVTC', p50: 12, p95: 18, color: '#F57C00' },
  { label: 'Mock', p50: 15, p95: 22, color: '#8B5CF6' },
  { label: 'Claude Haiku', p50: 320, p95: 580, color: '#E40520' },
  { label: 'Gemma 2B', p50: 850, p95: 1200, color: '#6677AA' },
]

function BigMetric({ m, delay }) {
  const val = useCountUp(m.value, 1200, delay)
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay / 1000, duration: 0.5, ease: 'backOut' }}
      className="card p-5 flex flex-col items-center text-center relative overflow-hidden"
    >
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: `radial-gradient(circle at 50% 100%, ${m.color}08 0%, transparent 70%)` }}
      />
      <span className="text-2xl mb-2">{m.icon}</span>
      <div className="text-4xl font-black" style={{ color: m.color }}>
        {val}{m.suffix}
      </div>
      <div className="text-sm font-semibold text-white mt-1">{m.label}</div>
      <div className="text-[11px] text-[#556677] mt-0.5">{m.sub}</div>
    </motion.div>
  )
}

function LatencyBar({ item, maxVal, delay }) {
  const [animate, setAnimate] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setAnimate(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  const pct50 = Math.max((item.p50 / maxVal) * 100, 2)
  const pct95 = Math.max((item.p95 / maxVal) * 100, 2)

  return (
    <motion.div
      initial={{ opacity: 0, x: -15 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: delay / 1000 }}
      className="flex items-center gap-3"
    >
      <div className="w-24 text-xs text-[#6677AA] text-right flex-shrink-0">{item.label}</div>
      <div className="flex-1 relative h-5 bg-[#0D1526] rounded overflow-hidden">
        <motion.div
          className="absolute left-0 top-0 h-full rounded"
          style={{ background: `${item.color}44` }}
          initial={{ width: 0 }}
          animate={{ width: animate ? `${pct95}%` : 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
        <motion.div
          className="absolute left-0 top-0 h-full rounded"
          style={{ background: item.color }}
          initial={{ width: 0 }}
          animate={{ width: animate ? `${pct50}%` : 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
      <div className="w-20 text-right text-[11px] font-mono flex-shrink-0">
        <span style={{ color: item.color }}>
          {item.p50 >= 1000 ? `${(item.p50/1000).toFixed(2)}s` : `${item.p50}ms`}
        </span>
        <span className="text-[#334455] ml-1 text-[10px]">P50</span>
      </div>
    </motion.div>
  )
}

export default function MetricsSlide() {
  const maxLatency = Math.max(...LATENCY.map(l => l.p95))

  return (
    <div className="w-full h-full flex flex-col justify-center px-12 py-10 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-2">06 / Performance</div>
        <h2 className="text-4xl font-black">
          Messbare <span className="text-gradient">Ergebnisse</span>
        </h2>
        <p className="text-[#8899AA] mt-1">Production-Ready · Docker · i7-11700K · 16GB RAM</p>
      </motion.div>

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Big 4 metrics */}
        <div className="grid grid-cols-2 gap-3">
          {BIG_METRICS.map((m, i) => (
            <BigMetric key={m.label} m={m} delay={i * 150} />
          ))}
        </div>

        {/* Right: Latency */}
        <div className="card p-5">
          <div className="text-xs font-mono text-[#445566] uppercase tracking-widest mb-4">
            Latenz-Benchmark (P50)
          </div>
          <div className="space-y-3">
            {LATENCY.map((item, i) => (
              <LatencyBar key={item.label} item={item} maxVal={maxLatency} delay={300 + i * 100} />
            ))}
          </div>
          <div className="mt-4 flex gap-3 text-[10px] font-mono text-[#334455]">
            <span className="flex items-center gap-1"><span className="w-3 h-2 rounded" style={{ background: '#00A0DC' }} /> P50</span>
            <span className="flex items-center gap-1"><span className="w-3 h-2 rounded" style={{ background: '#00A0DC44' }} /> P95</span>
          </div>

          {/* Compression table */}
          <div className="mt-4 pt-4 border-t border-[rgba(0,160,220,0.1)]">
            <div className="text-[10px] font-mono text-[#445566] uppercase tracking-widest mb-2">Kompressions-Benchmark</div>
            <table className="w-full text-[11px] font-mono">
              <thead>
                <tr className="text-[#334455]">
                  <th className="text-left font-normal pb-1">Dokument</th>
                  <th className="text-right font-normal pb-1">Original</th>
                  <th className="text-right font-normal pb-1 text-[#00C853]">Komprimiert</th>
                </tr>
              </thead>
              <tbody className="text-[#6677AA]">
                {[
                  ['Wartungsprotokoll', '1.847 T', '187 T (−88%)'],
                  ['QA-Bericht', '2.891 T', '223 T (−92%)'],
                  ['OBD-Fehler', '45 T', '15 T (−67%)'],
                  ['Produktionsauftrag', '1.337 T', '166 T (−88%)'],
                ].map(([name, orig, comp]) => (
                  <tr key={name} className="border-t border-[rgba(0,160,220,0.06)]">
                    <td className="py-1">{name}</td>
                    <td className="py-1 text-right text-[#E40520]">{orig}</td>
                    <td className="py-1 text-right text-[#00C853]">{comp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
