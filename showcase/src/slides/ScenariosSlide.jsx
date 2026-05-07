import { motion } from 'framer-motion'

const SCENARIOS = [
  {
    id: 'xentry',
    title: 'XENTRY Diagnose-Logs',
    icon: '🔧',
    color: '#E40520',
    case: 'After-Sales Excellence',
    desc: 'Reduktion von Diagnose-Logs mit 10.000 Zeilen auf die relevanten 20 Zeilen "Fault State".',
    impact: 'Massive Token-Ersparnis bei der Fehlerursachenanalyse im Werkstatt-Einsatz.',
    example: '10k Zeilen → 20 Relevante Zeilen (KVTC Filter)'
  },
  {
    id: 'mo360',
    title: 'MO360 Produktion',
    icon: '🏭',
    color: '#00A0DC',
    case: 'Factory 56 / Digitaler Zwilling',
    desc: 'Relevanzfilter für Schichtberichte. Filtert "Normalbetrieb-Rauschen" für Qualitätsingenieure.',
    impact: 'Präzise Fehleridentifikation ohne redundante Datenlast.',
    example: 'Schichtbericht (Redundant) → Präzise Anomalie (KVTC)'
  },
  {
    id: 'supply',
    title: 'Supply Chain Reporting',
    icon: '📦',
    color: '#00C853',
    case: 'Risiko-Management',
    desc: 'Bereinigung redundanter Lieferanten-Updates durch semantische Deduplizierung.',
    impact: 'Beschleunigt Risiko-Assessments für das Management durch Fokus auf Abweichungen.',
    example: '50 Updates → 1 Konziser Statusbericht'
  }
]

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.15 } }
}

const item = {
  hidden: { opacity: 0, scale: 0.9 },
  show: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: "easeOut" } }
}

export default function ScenariosSlide() {
  return (
    <div className="w-full h-full flex flex-col justify-center px-12 py-10 max-w-6xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-2">03 / Top Use Cases (ROI)</div>
        <h2 className="text-4xl font-black">
          Der <span className="text-gradient">ROI-Nachweis</span>
        </h2>
        <p className="text-[#8899AA] mt-1 text-lg">Konkrete Wertschöpfung in der Mercedes-Benz Systemlandschaft</p>
      </motion.div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-3 gap-6"
      >
        {SCENARIOS.map((s) => (
          <motion.div
            key={s.id}
            variants={item}
            className="card p-6 relative overflow-hidden group hover:border-[#00A0DC55] transition-colors flex flex-col"
          >
            <div
              className="absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 opacity-5 group-hover:opacity-10 transition-opacity"
              style={{ background: s.color, borderRadius: '50%' }}
            />

            <div className="flex items-center gap-3 mb-4">
              <span className="text-4xl">{s.icon}</span>
              <div>
                <h3 className="font-bold text-white text-lg leading-tight">{s.title}</h3>
                <span className="text-[10px] font-mono uppercase tracking-widest" style={{ color: s.color }}>
                  {s.case}
                </span>
              </div>
            </div>

            <p className="text-sm text-[#8899AA] mb-6 leading-relaxed flex-grow">
              {s.desc}
            </p>

            <div className="space-y-3 mt-auto">
              <div className="flex items-start gap-2">
                <span className="text-[#00C853] text-[12px] mt-1">✓</span>
                <span className="text-[12px] text-[#B0C4D8] font-medium">{s.impact}</span>
              </div>
              <div className="bg-[#0D1526] p-3 rounded border border-[rgba(0,160,220,0.1)]">
                <div className="text-[10px] font-mono text-[#445566] uppercase mb-1">Impact</div>
                <div className="text-[11px] font-mono text-[#6677AA] truncate">{s.example}</div>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}
