import { motion } from 'framer-motion'

const problems = [
  {
    icon: '💸',
    title: 'Token-Kosten explodieren',
    desc: 'Ein Wartungsprotokoll = ~1.800 LLM-Tokens. Bei 10.000 Dokumenten/Tag = 18M Tokens täglich.',
    color: '#E40520',
  },
  {
    icon: '🔐',
    title: 'DSGVO: PII im Klartext',
    desc: 'Rohdokumente enthalten FIN, Personal-IDs, E-Mails – dürfen nie unkontrolliert zu einem LLM.',
    color: '#F57C00',
  },
  {
    icon: '🌐',
    title: 'Kein Cloud-Zwang',
    desc: 'Sicherheitskritische Fahrzeugdaten müssen air-gap-fähig bleiben – kein Internet-Upload.',
    color: '#8B5CF6',
  },
  {
    icon: '⚡',
    title: 'Realtime-Anforderung',
    desc: 'OBD-Fehler P0300 (Zündaussetzer) muss in <1 Sekunde als P1_KRITISCH eskaliert werden.',
    color: '#00A0DC',
  },
]

const solution = [
  { icon: '📦', text: '88% Token-Reduktion via KVTC' },
  { icon: '🔒', text: 'PII nie das System verlässt' },
  { icon: '🏠', text: 'Ollama Gemma 2B: 100% lokal' },
  { icon: '⚡', text: '8ms Triage · 1ms Cache-Hit' },
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
        <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-2">02 / Challenge</div>
        <h2 className="text-4xl font-black">
          Warum ist das <span className="text-gradient-red">schwierig?</span>
        </h2>
        <p className="text-[#8899AA] mt-2 text-lg">
          Industrielle KI-Integration bei Daimler Buses – 4 kritische Anforderungen
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
              ✓ CompText Lösung
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
              <span className="text-3xl font-black text-gradient">~90%</span>
              <span className="text-sm text-[#8899AA] ml-2">Token-Kosteneinsparung</span>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
