"""
Daimler Buses CompText – Streamlit Dashboard
Startbefehl: streamlit run dashboard.py
"""

from __future__ import annotations

import json

import streamlit as st

from config import DEFAULT_CONFIG
from src.agents.analysis_agent import AnalysisAgent
from src.agents.intake_agent import IntakeAgent
from src.agents.triage_agent import TriageAgent
from src.core.kvtc import IndustrialKVTCStrategy, run_benchmark
from src.models.schemas import ProcessPriority

# ---------------------------------------------------------------------------
# Seiten-Konfiguration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Daimler Buses – CompText",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Daimler-Farben
DAIMLER_BLUE  = "#003366"
DAIMLER_CYAN  = "#00B5E2"
PRIO_COLORS   = {
    ProcessPriority.P1_KRITISCH: "#D32F2F",
    ProcessPriority.P2_DRINGEND: "#F57C00",
    ProcessPriority.P3_ROUTINE:  "#388E3C",
}

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Mercedes-Benz_Logo_2010.svg/320px-Mercedes-Benz_Logo_2010.svg.png",
        width=80,
    )
    st.title("Daimler Buses\nCompText")
    st.caption("Prozessautomatisierung – KI-Analyse")
    st.divider()

    backend_label = st.selectbox(
        "LLM-Backend",
        options=["Mock (Demo)", "Ollama Gemma 2B", "Claude Haiku"],
        index=0,
    )
    backend_map = {
        "Mock (Demo)":      "mock",
        "Ollama Gemma 2B":  "ollama_gemma",
        "Claude Haiku":     "anthropic",
    }

    st.divider()
    st.markdown("**Über CompText**")
    st.markdown(
        "Token-Komprimierung für industrielle Prozessdokumente. "
        "Basiert auf MedGemma-CompText / CompText-Monorepo-X."
    )
    st.markdown("v0.1 · Apache 2.0")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_analyse, tab_benchmark, tab_info = st.tabs(
    ["📋 Dokument-Analyse", "📊 Benchmark", "ℹ️ Systeminfo"]
)

# ---------------------------------------------------------------------------
# Tab: Dokument-Analyse
# ---------------------------------------------------------------------------

with tab_analyse:
    st.header("Dokument-Analyse")

    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("Eingabe")
        doc_text = st.text_area(
            "Prozessdokument einfügen",
            height=300,
            placeholder=(
                "Wartungsprotokoll, OBD-Fehlercodes, QA-Bericht, "
                "Produktionsauftrag, Lieferschein ...\n\n"
                "Beispiel:\nWartungsauftrag Nr. 2024-08-1234\n"
                "Fahrzeug: Tourismo M, Bj. 2019\n"
                "FIN: WDB906232N3123456\n"
                "Kilometerstand: 145.000 km\n"
                "Techniker: P12345\n"
                "Fehlercode: P0300 – Zündaussetzer Zylinder 1\n"
                "Maßnahme: Zündkerzen erneuert, Zündkabel geprüft\n"
                "Nächster Service: 160.000 km"
            ),
            key="doc_input",
        )
        quelle = st.text_input("Quelle / System", value="Werkstatt-SAP", key="quelle")

        analyse_btn = st.button("Analysieren ▶", type="primary", use_container_width=True)

    with col_output:
        st.subheader("Ergebnis")

        if analyse_btn and doc_text.strip():
            cfg = DEFAULT_CONFIG
            from src.agents.analysis_agent import AnalysisConfig, ModelBackend
            cfg.analysis = AnalysisConfig(
                backend=ModelBackend(backend_map[backend_label]),
                model_id=cfg.analysis.model_id,
                anthropic_model=cfg.analysis.anthropic_model,
            )

            with st.spinner("Verarbeite …"):
                intake_agent   = IntakeAgent(IndustrialKVTCStrategy(
                    header_lines=cfg.kvtc_header_lines,
                    window_lines=cfg.kvtc_window_lines,
                ))
                triage_agent   = TriageAgent()
                analysis_agent = AnalysisAgent(cfg.analysis)

                intake_result  = intake_agent.process(doc_text, quelle=quelle)
                triage_result  = triage_agent.classify(intake_result.dokument)
                analyse_result = analysis_agent.analyze(
                    intake_result.dokument,
                    intake_result.kvtc,
                    triage_result,
                )

            prio = analyse_result.prioritaet
            prio_color = PRIO_COLORS.get(prio, "#607D8B")

            st.markdown(
                f"<div style='background:{prio_color};color:white;padding:8px 16px;"
                f"border-radius:6px;font-weight:bold;font-size:1.1em'>"
                f"Priorität: {prio.value}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("")

            st.markdown(f"**Zusammenfassung:** {analyse_result.zusammenfassung}")

            if analyse_result.massnahmen:
                st.markdown("**Empfohlene Maßnahmen:**")
                for m in analyse_result.massnahmen:
                    st.markdown(f"- {m}")

            if analyse_result.erkannte_fehlercodes:
                st.markdown(
                    "**OBD-Codes:** `" + "` `".join(analyse_result.erkannte_fehlercodes) + "`"
                )

            st.divider()
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Token original",     f"{analyse_result.token_original:,}")
            col_m2.metric("Token komprimiert",  f"{analyse_result.token_komprimiert:,}")
            col_m3.metric("Einsparung",          f"{analyse_result.token_einsparung_pct:.1f}%")

            col_m4, col_m5 = st.columns(2)
            col_m4.metric("Konfidenz",  f"{analyse_result.konfidenz:.0%}")
            col_m5.metric("Latenz",     f"{analyse_result.latenz_ms:.1f} ms")

            if intake_result.bereinigungen:
                with st.expander("🔒 DSGVO-Bereinigungen"):
                    for b in intake_result.bereinigungen:
                        st.markdown(f"- {b}")

            with st.expander("🔧 KVTC-Frame (komprimiert)"):
                st.code(intake_result.kvtc.frame, language="text")

        elif analyse_btn:
            st.warning("Bitte ein Dokument eingeben.")

# ---------------------------------------------------------------------------
# Tab: Benchmark
# ---------------------------------------------------------------------------

with tab_benchmark:
    st.header("KVTC-Benchmark")
    st.markdown(
        "Simuliert Komprimierung über typische Daimler-Buses-Dokumente "
        "und misst Token-Einsparung sowie Latenz."
    )

    if st.button("Benchmark starten", type="primary"):
        test_cases = [
            {
                "label": "Kurzes Wartungsprotokoll",
                "text": (
                    "Wartungsauftrag 2024-001\nFahrzeug: Citaro G\nKilometerstand: 80.000\n"
                    "Fehler: Klimaanlage ausgefallen\nMaßnahme: Kältemittel nachgefüllt"
                ),
            },
            {
                "label": "OBD-Fehlerspeicher (lang)",
                "text": "\n".join(
                    [f"P{1000+i}: Fehler in Steuergerät {i % 5} – Sensor außer Bereich"
                     for i in range(50)]
                ),
            },
            {
                "label": "QA-Prüfbericht",
                "text": (
                    "Prüfbericht QA-2024-0815\nFahrzeug-FIN: WDB906232N3123456\n"
                    "Prüfdatum: 15.08.2024\nPrüfer: P54321\n"
                    + "\n".join(
                        [f"Prüfpunkt {i+1}: {'OK' if i % 3 != 0 else 'NACHARBEIT'} – "
                         f"{'Bremse' if i % 2 == 0 else 'Lenkung'} {i}"
                         for i in range(40)]
                    )
                ),
            },
            {
                "label": "Produktionsauftrag Taktblatt",
                "text": (
                    "Produktionsauftrag: PA-2024-4567\nFahrzeugtyp: Tourismo RHD\n"
                    "Arbeitsstation: Station 12 – Innenausbau\n"
                    "Soll-Takt: 45 min\nIst-Takt: 52 min (+15%)\n"
                    "Abweichung: Teileengpass Sitzgestell PN 9876543\n"
                    + "\n".join([f"Schritt {i+1}: Arbeitsschritt abgeschlossen" for i in range(30)])
                ),
            },
            {
                "label": "Historisches Wartungsarchiv (Stress)",
                "text": "\n".join(
                    [f"Eintrag {i+1} | Datum: {(i%28)+1:02d}.{(i%12)+1:02d}.202{i%4} | "
                     f"km: {50000 + i*2000} | Maßnahme: Routineinspektion {i%5}"
                     for i in range(200)]
                ),
            },
        ]

        with st.spinner("Benchmark läuft …"):
            results = run_benchmark(test_cases)

        col_b1, col_b2, col_b3 = st.columns(3)
        col_b1.metric("Ø Token-Einsparung", f"{results['avg_token_reduction_pct']:.1f}%")
        col_b2.metric("Ø Latenz",           f"{results['avg_latency_ms']:.3f} ms")
        col_b3.metric("Test-Cases",         results["total_cases"])

        st.divider()
        for case in results["cases"]:
            with st.expander(f"📄 {case['label']}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Original",       f"{case['original_tokens']:,} Tokens")
                c2.metric("Komprimiert",    f"{case['compressed_tokens']:,} Tokens")
                c3.metric("Einsparung",     f"{case['reduction_pct']:.1f}%")
                c4.metric("Latenz",         f"{case['latency_ms']:.3f} ms")
                st.caption(f"Checksum: `{case['checksum']}`")

# ---------------------------------------------------------------------------
# Tab: Systeminfo
# ---------------------------------------------------------------------------

with tab_info:
    st.header("Systeminfo")

    col_i1, col_i2 = st.columns(2)

    with col_i1:
        st.markdown("### Architektur")
        st.markdown(
            """
| Layer | Komponente | Funktion |
|-------|-----------|---------|
| 1 | **IntakeAgent** | DSGVO-Bereinigung, Typ-Erkennung, KVTC |
| 2 | **TriageAgent** | P1/P2/P3 Priorität (regelbasiert) |
| 3 | **AnalysisAgent** | LLM-Inferenz (Gemma / Claude) |

**KVTC 4-Layer:**
- **K** Key – Feldbezeichner
- **V** Value – Feldwerte
- **T** Type – Datentypkategorien
- **C** Code – OBD, SAP-Nummern, FIN-Fragmente

**Sandwich-Zonen:**
- Header → Lossless (SOPs, Stammdaten)
- Middle → Aggressiv komprimiert (Historik)
- Window → Lossless (aktuelle Daten)
            """
        )

    with col_i2:
        st.markdown("### Anwendungsfälle")
        st.markdown(
            """
**Daimler Buses Prozessautomatisierung:**

- 🔧 **Predictive Maintenance** – Wartungsbedarf früh erkennen
- 🔍 **OBD-Analyse** – Fehlercodes priorisieren & Maßnahmen ableiten
- ✅ **QA-Prüfberichte** – Beanstandungen klassifizieren
- 🏭 **Produktionsoptimierung** – Taktabweichungen analysieren
- 📦 **Lieferkette** – Engpässe und Verzögerungen erkennen

**Edge-Fähigkeit:**
Läuft lokal mit Ollama Gemma 2B – kein Cloud-Zwang,
DSGVO-konform durch One-Way-Hashing & PHI-Scrubbing.
            """
        )

    st.divider()
    st.caption(
        "Basiert auf MedGemma-CompText (ProfRandom92) · "
        "CompText-Monorepo-X (4-Layer KVTC, serializeFrame) · "
        "Apache 2.0 Lizenz"
    )
