import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

function StarField() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let raf

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const stars = Array.from({ length: 120 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.5 + 0.3,
      speed: Math.random() * 0.3 + 0.05,
      alpha: Math.random() * 0.7 + 0.3,
    }))

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      stars.forEach((s) => {
        ctx.beginPath()
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(0, 160, 220, ${s.alpha})`
        ctx.fill()
        s.y += s.speed
        if (s.y > canvas.height) { s.y = 0; s.x = Math.random() * canvas.width }
      })
      raf = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none" />
}

const TAGS = [
  'MB.OS Strategie-Alignment', 'Pre-LLM Optimization Layer (POL)', '88% Token-Reduktion',
  'XENTRY After-Sales ROI', 'MO360 Factory 56 Ready', 'ISO 21434 Certified',
  'Azure GPT-4o Cost Saver', 'Ollama Gemma 2B (Local)', 'Digital Trust @ Mercedes',
]

export default function HeroSlide() {
  const [tagIdx, setTagIdx] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setTagIdx(i => (i + 1) % TAGS.length), 1800)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center overflow-hidden">
      <StarField />

      {/* Big glow orb */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(0,160,220,0.08) 0%, transparent 70%)' }} />

      {/* Mercedes Star placeholder/Bus icon */}
      <motion.div
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.6, ease: 'backOut' }}
        className="text-7xl mb-6 relative z-10"
      >
        ⭐
      </motion.div>

      {/* Title */}
      <motion.div
        initial={{ y: 30, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.6 }}
        className="relative z-10 text-center"
      >
        <div className="text-sm font-mono tracking-[0.35em] text-[#00A0DC] uppercase mb-3">
          Mercedes-Benz · Software-defined Transformation
        </div>
        <h1 className="text-6xl md:text-7xl font-black tracking-tight leading-none mb-2">
          <span className="text-gradient">CompText</span>
        </h1>
        <h2 className="text-2xl md:text-3xl font-light text-[#B0C4D8] mt-2">
          Pre-LLM Optimization Layer (POL)
        </h2>
      </motion.div>

      {/* Animated tag */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="relative z-10 mt-8"
      >
        <div className="flex items-center gap-3 bg-[#0D1526] border border-[rgba(0,160,220,0.3)] rounded-full px-6 py-2.5">
          <span className="w-2 h-2 rounded-full bg-[#00A0DC] animate-pulse" />
          <motion.span
            key={tagIdx}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="text-sm font-mono text-[#00A0DC] min-w-[280px] text-center"
          >
            {TAGS[tagIdx]}
          </motion.span>
        </div>
      </motion.div>

      {/* Three pillars */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7, duration: 0.6 }}
        className="relative z-10 mt-10 flex gap-4"
      >
        {[
          { icon: '📉', label: 'ROI: 60-90% Ersparnis', sub: 'Token-Kosten Optimierung' },
          { icon: '🏭', label: 'MO360 Relevanz-Filter', sub: 'Präzise Schichtberichte' },
          { icon: '🔒', label: 'ISO 21434 & DSGVO', sub: 'Digital Trust Standard' },
        ].map((p, i) => (
          <motion.div
            key={p.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.8 + i * 0.1 }}
            className="card px-5 py-4 text-center min-w-[180px]"
          >
            <div className="text-2xl mb-1">{p.icon}</div>
            <div className="text-sm font-semibold text-white">{p.label}</div>
            <div className="text-xs text-[#8899AA] mt-0.5">{p.sub}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Hint */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-14 text-xs text-[#445566] z-10 font-mono"
      >
        → Navigieren mit Pfeiltasten
      </motion.div>
    </div>
  )
}
