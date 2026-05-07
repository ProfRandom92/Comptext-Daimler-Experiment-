import { useState, useEffect, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import HeroSlide from './slides/HeroSlide.jsx'
import ProblemSlide from './slides/ProblemSlide.jsx'
import ArchitectureSlide from './slides/ArchitectureSlide.jsx'
import KVTCSlide from './slides/KVTCSlide.jsx'
import SecuritySlide from './slides/SecuritySlide.jsx'
import MetricsSlide from './slides/MetricsSlide.jsx'
import DemoSlide from './slides/DemoSlide.jsx'

const SLIDES = [
  { id: 'hero',         component: HeroSlide,         label: 'Start' },
  { id: 'problem',      component: ProblemSlide,       label: 'Challenge' },
  { id: 'architecture', component: ArchitectureSlide,  label: 'Architektur' },
  { id: 'kvtc',         component: KVTCSlide,          label: 'KVTC' },
  { id: 'security',     component: SecuritySlide,      label: 'DSGVO' },
  { id: 'metrics',      component: MetricsSlide,       label: 'Metriken' },
  { id: 'demo',         component: DemoSlide,          label: 'Live Demo' },
]

const variants = {
  enter: (dir) => ({ x: dir > 0 ? '100%' : '-100%', opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit:  (dir) => ({ x: dir > 0 ? '-100%' : '100%', opacity: 0 }),
}

export default function App() {
  const [[page, dir], setPage] = useState([0, 0])

  const goTo = useCallback((next) => {
    setPage(([cur]) => {
      const clamped = Math.max(0, Math.min(SLIDES.length - 1, next))
      return [clamped, next > cur ? 1 : -1]
    })
  }, [])

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ')
        goTo(page + 1)
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp')
        goTo(page - 1)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [page, goTo])

  const SlideComponent = SLIDES[page].component

  return (
    <div className="relative w-full h-full overflow-hidden grid-bg select-none">
      {/* Top progress bar */}
      <motion.div
        className="absolute top-0 left-0 h-[2px] z-50"
        style={{ background: 'linear-gradient(90deg, #00A0DC, #0DCFFF)' }}
        animate={{ width: `${((page + 1) / SLIDES.length) * 100}%` }}
        transition={{ duration: 0.5, ease: 'easeInOut' }}
      />

      {/* Slide area */}
      <AnimatePresence mode="wait" custom={dir}>
        <motion.div
          key={page}
          custom={dir}
          variants={variants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          className="absolute inset-0"
        >
          <SlideComponent />
        </motion.div>
      </AnimatePresence>

      {/* Bottom navigation */}
      <div className="absolute bottom-6 left-0 right-0 flex items-center justify-center gap-6 z-50">
        {/* Prev */}
        <button
          onClick={() => goTo(page - 1)}
          disabled={page === 0}
          className="text-sm font-medium text-[#8899AA] hover:text-white transition-colors disabled:opacity-20 disabled:cursor-not-allowed px-3 py-1"
        >
          ← Zurück
        </button>

        {/* Dots */}
        <div className="flex items-center gap-2">
          {SLIDES.map((s, i) => (
            <button
              key={s.id}
              onClick={() => goTo(i)}
              title={s.label}
              className={`dot ${i === page ? 'active' : ''}`}
            />
          ))}
        </div>

        {/* Next */}
        <button
          onClick={() => goTo(page + 1)}
          disabled={page === SLIDES.length - 1}
          className="text-sm font-medium text-[#8899AA] hover:text-white transition-colors disabled:opacity-20 disabled:cursor-not-allowed px-3 py-1"
        >
          Weiter →
        </button>
      </div>

      {/* Slide counter */}
      <div className="absolute top-4 right-6 text-xs text-[#556677] z-50 font-mono">
        {String(page + 1).padStart(2, '0')} / {String(SLIDES.length).padStart(2, '0')}
      </div>
    </div>
  )
}
