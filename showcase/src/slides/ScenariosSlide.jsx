import { motion } from 'framer-motion'

const SCENARIOS = [
  {
    id: 'token',
    title: 'Token Reduction',
    icon: '📉',
    color: '#00C853',
    case: 'Predictive Maintenance',
    desc: 'Langzeit-Monitoring von Fahrzeugflotten erzeugt Gigabytes an Logdaten.',
    impact: '90% Reduktion der Cloud-Transferkosten und LLM-Input-Gebühren.',
    example: 'Wartungsintervall-Historie (10MB) → KVTC-Frame (1.2MB)'
  },
  {
    id: 'privacy',
    title: 'Datenschutz (DSGVO)',
    icon: '🛡️',
    color: '#00A0DC',
    case: 'Externes Audit',
    desc: 'Analyse von Werkstattberichten durch Drittanbieter oder Cloud-LLMs.',
    impact: 'Automatische Maskierung von FIN, Namen und Telefonnummern vor dem Upload.',
    example: 'Max Mustermann (FIN: WDB...) → PERS_HASH (FIN_***123)'
  },
  {
    id: 'security',
    title: 'Sicherheit',
    icon: '🔒',
    color: '#E40520',
    case: 'Air-Gap Diagnostics',
    desc: 'Einsatz in geschlossenen Netzwerken ohne Internetverbindung.',
    impact: 'Lokale Inferenz mit Gemma 2B verhindert Datenabfluss aus dem Werkstatt-LAN.',
    example: 'Offline-Betrieb auf robusten Werkstatt-Tablets (Termux/Docker)'
  },
  {
    id: 'performance',
    title: 'Performance',
    icon: '⚡',
    color: '#F57C00',
    case: 'Real-Time Triage',
    desc: 'Sofortige Reaktion auf kritische OBD-Fehler während der Fahrt.',
    impact: 'Latenz < 20ms für die Klassifizierung kritischer Fehler (P1_KRITISCH).',
    example: 'P0524 (Öldruck) → Sofort-Stopp-Warnung in Millisekunden'
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
        <div className="text-xs font-mono tracking-widest text-[#00A0DC] uppercase mb-2">03 / Einsatz-Szenarien</div>
        <h2 className="text-4xl font-black">
          CompText <span className="text-gradient">in der Praxis</span>
        </h2>
        <p className="text-[#8899AA] mt-1 text-lg">Optimierungspotenziale entlang der Wertschöpfungskette</p>
      </motion.div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 gap-4"
      >
        {SCENARIOS.map((s) => (
          <motion.div
            key={s.id}
            variants={item}
            className="card p-5 relative overflow-hidden group hover:border-[#00A0DC55] transition-colors"
          >
            <div
              className="absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 opacity-5 group-hover:opacity-10 transition-opacity"
              style={{ background: s.color, borderRadius: '50%' }}
            />

            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">{s.icon}</span>
              <div>
                <h3 className="font-bold text-white text-lg leading-tight">{s.title}</h3>
                <span className="text-[10px] font-mono uppercase tracking-widest" style={{ color: s.color }}>
                  {s.case}
                </span>
              </div>
            </div>

            <p className="text-xs text-[#8899AA] mb-4 leading-relaxed">
              {s.desc}
            </p>

            <div className="space-y-2 mt-auto">
              <div className="flex items-start gap-2">
                <span className="text-[#00C853] text-[10px] mt-1">✓</span>
                <span className="text-[11px] text-[#B0C4D8] font-medium">{s.impact}</span>
              </div>
              <div className="bg-[#0D1526] p-2 rounded border border-[rgba(0,160,220,0.1)]">
                <div className="text-[9px] font-mono text-[#445566] uppercase mb-1">Beispiel</div>
                <div className="text-[10px] font-mono text-[#6677AA] truncate">{s.example}</div>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}
