import { motion } from 'framer-motion'

const problems = [
  {
    icon: '💸',
    title: 'Explodierende Token-Kosten',
    desc: 'Mercedes-Benz skaliert KI-Agenten massiv. Ohne Filterung steigen die Azure GPT-4o Kosten linear mit der Nutzung.',
    color: '#E40520',
  },
  {
    icon: '🔐',
    title: 'Digital Trust & Compliance',
    desc: 'Sensible Daten (XENTRY, MO360) erfordern strikte Maskierung (Art. 25 DSGVO) und Rückverfolgbarkeit (ISO 21434).',
    color: '#F57C00',
  },
  {
    icon: '⚡',
    title: 'Latenz vs. Produktivität',
    desc: 'Ungefilterte Dokumente verlangsamen die Inferenz. Ziel: 20% Produktivitätssteigerung bis 2025 erfordert Echtzeit-Speed.',
    color: '#00A0DC',
  },
  {
    icon: '🏠',
    title: 'Datensouveränität',
    desc: 'Industrielle IP darf das Mercedes-Netzwerk nicht unkontrolliert verlassen. Cloud-Zwang ist ein Risiko.',
    color: '#8B5CF6',
  },
]

const solution = [
  { icon: '🛡️', text: 'Pre-LLM Optimization Layer (POL)' },
  { icon: '📉', text: '60-90% Kostensenkung via KVTC' },
  { icon: '🔒', text: 'ISO 21434 & GDPR by Design' },
  { icon: '⚡', text: '3.24x schnellere Inferenz' },
]

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
}
const item = {
  hidden: { opacity: 0, x: -20 },
  show:   { opacity: 1, x: 0, transition: { duration: 0.4 } },
}

export default function ProblemSlide() {
  return (
    <div className="w-full h-full flex flex-col justify-center px-12 py-16 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-2">02 / Die Herausforderung</div>
        <h2 className="text-4xl font-black">
          Warum <span className="text-gradient-red">Pre-LLM Optimization?</span>
        </h2>
        <p className="text-[#8899AA] mt-2 text-lg">
          Skalierung der KI-Agenten bei Mercedes-Benz ohne Budget-Explosion
        </p>
      </motion.div>

      <div className="grid grid-cols-2 gap-6 mb-10">
        {/* Problems */}
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-3">
          {problems.map((p) => (
            <motion.div
              key={p.title}
              variants={item}
              className="card flex items-start gap-4 p-4"
            >
              <span className="text-2xl flex-shrink-0">{p.icon}</span>
              <div>
                <div className="font-semibold text-white text-sm mb-0.5" style={{ color: p.color }}>
                  {p.title}
                </div>
                <div className="text-xs text-[#8899AA] leading-relaxed">{p.desc}</div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Solution column */}
        <div className="flex flex-col justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
            className="card p-6"
            style={{ borderColor: 'rgba(0,160,220,0.4)' }}
          >
            <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-4">
              ✓ CompText Strategie
            </div>
            <div className="space-y-3">
              {solution.map((s, i) => (
                <motion.div
                  key={s.text}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + i * 0.1 }}
                  className="flex items-center gap-3"
                >
                  <span className="text-xl">{s.icon}</span>
                  <span className="text-sm text-[#B0C4D8]">{s.text}</span>
                </motion.div>
              ))}
            </div>

            <motion.div
              initial={{ width: 0 }}
              animate={{ width: '100%' }}
              transition={{ delay: 1.1, duration: 0.8 }}
              className="mt-6 h-[1px] bg-gradient-to-r from-[#00A0DC] to-transparent"
            />

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.3 }}
              className="mt-4 text-center"
            >
              <span className="text-3xl font-black text-gradient">20%</span>
              <span className="text-sm text-[#8899AA] ml-2">Produktivitätsziel (2025)</span>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
