"""
Daimler Buses CompText – Streamlit Dashboard
Startbefehl: streamlit run dashboard.py
"""

from __future__ import annotations

import csv
import io
import json as _json
from typing import Any

import streamlit as st

from config import DEFAULT_CONFIG, AppConfig
from src.agents.analysis_agent import AnalysisAgent, AnalysisConfig, ModelBackend
from src.agents.intake_agent import IntakeAgent
from src.agents.triage_agent import TriageAgent
from src.core.kvtc import IndustrialKVTCStrategy, run_benchmark
from src.models.schemas import ProcessPriority

st.set_page_config(
    page_title="Daimler Buses – CompText",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

_PRIO_COLORS = {
    ProcessPriority.P1_KRITISCH: "#D32F2F",
    ProcessPriority.P2_DRINGEND: "#F57C00",
    ProcessPriority.P3_ROUTINE:  "#388E3C",
}

_BACKEND_OPTIONS = {
    "Mock (Demo)":     ModelBackend.MOCK,
    "Ollama Gemma 2B": ModelBackend.OLLAMA_GEMMA,
    "Claude Haiku":    ModelBackend.ANTHROPIC,
}


def _result_to_json(analyse_result: Any, intake_result: Any) -> str:
    return _json.dumps({
        "eingabe_checksum": analyse_result.eingabe_checksum,
        "prioritaet": analyse_result.prioritaet.value,
        "doc_type": intake_result.dokument.doc_type.value,
        "zusammenfassung": analyse_result.zusammenfassung,
        "massnahmen": analyse_result.massnahmen,
        "erkannte_fehlercodes": analyse_result.erkannte_fehlercodes,
        "konfidenz": analyse_result.konfidenz,
        "token_original": analyse_result.token_original,
        "token_komprimiert": analyse_result.token_komprimiert,
        "token_einsparung_pct": analyse_result.token_einsparung_pct,
        "latenz_ms": analyse_result.latenz_ms,
        "modell_id": analyse_result.modell_id,
        "bereinigungen": intake_result.bereinigungen,
    }, ensure_ascii=False, indent=2)


def _result_to_csv(analyse_result: Any, intake_result: Any) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "checksum", "prioritaet", "doc_type", "zusammenfassung",
        "obd_codes", "konfidenz", "token_original", "token_komprimiert",
        "token_einsparung_pct", "latenz_ms", "modell_id",
    ])
    writer.writerow([
        analyse_result.eingabe_checksum,
        analyse_result.prioritaet.value,
        intake_result.dokument.doc_type.value,
        analyse_result.zusammenfassung,
        "; ".join(analyse_result.erkannte_fehlercodes),
        f"{analyse_result.konfidenz:.3f}",
        analyse_result.token_original,
        analyse_result.token_komprimiert,
        f"{analyse_result.token_einsparung_pct:.2f}",
        f"{analyse_result.latenz_ms:.1f}",
        analyse_result.modell_id,
    ])
    return buf.getvalue()


def _get_agents(backend: ModelBackend) -> tuple[IntakeAgent, TriageAgent, AnalysisAgent]:
    """Cache agents in session_state; rebuild only when backend changes."""
    key = f"agents_{backend.value}"
    if key not in st.session_state:
        cfg = AppConfig(
            analysis=AnalysisConfig(
                backend=backend,
                model_id=DEFAULT_CONFIG.analysis.model_id,
                anthropic_model=DEFAULT_CONFIG.analysis.anthropic_model,
            ),
            kvtc_header_lines=DEFAULT_CONFIG.kvtc_header_lines,
            kvtc_window_lines=DEFAULT_CONFIG.kvtc_window_lines,
        )
        st.session_state[key] = (
            IntakeAgent(IndustrialKVTCStrategy(cfg.kvtc_header_lines, cfg.kvtc_window_lines)),
            TriageAgent(),
            AnalysisAgent(cfg.analysis),
        )
    return st.session_state[key]


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

    selected_backend_label = st.selectbox("LLM-Backend", options=list(_BACKEND_OPTIONS), index=0)
    selected_backend = _BACKEND_OPTIONS[selected_backend_label]

    st.divider()
    st.markdown("**Über CompText**")
    st.markdown(
        "Token-Komprimierung für industrielle Prozessdokumente. "
        "Basiert auf MedGemma-CompText / CompText-Monorepo-X."
    )
    st.markdown("v0.2 · Apache 2.0")

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
        )
        quelle = st.text_input("Quelle / System", value="Werkstatt-SAP")
        analyse_btn = st.button("Analysieren ▶", type="primary", use_container_width=True)

    with col_output:
        st.subheader("Ergebnis")

        if analyse_btn and doc_text.strip():
            intake_agent, triage_agent, analysis_agent = _get_agents(selected_backend)

            with st.spinner("Verarbeite …"):
                intake_result  = intake_agent.process(doc_text, quelle=quelle)
                triage_result  = triage_agent.classify(intake_result.dokument)
                analyse_result = analysis_agent.analyze(
                    intake_result.dokument, intake_result.kvtc, triage_result
                )
                st.session_state["last_analyse_result"] = analyse_result
                st.session_state["last_intake_result"]  = intake_result

            prio = analyse_result.prioritaet
            st.markdown(
                f"<div style='background:{_PRIO_COLORS[prio]};color:white;padding:8px 16px;"
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
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Token original",    f"{analyse_result.token_original:,}")
            c2.metric("Token komprimiert", f"{analyse_result.token_komprimiert:,}")
            c3.metric("Einsparung",        f"{analyse_result.token_einsparung_pct:.1f}%")
            c4.metric("Konfidenz",         f"{analyse_result.konfidenz:.0%}")
            c5.metric("Latenz",            f"{analyse_result.latenz_ms:.1f} ms")

            if intake_result.bereinigungen:
                with st.expander("🔒 DSGVO-Bereinigungen"):
                    for b in intake_result.bereinigungen:
                        st.markdown(f"- {b}")

            with st.expander("🔧 KVTC-Frame (komprimiert)"):
                st.code(intake_result.kvtc.frame, language="text")

        elif analyse_btn:
            st.warning("Bitte ein Dokument eingeben.")

        # Export-Buttons – außerhalb des analyse_btn-Blocks, damit sie nach Streamlit-Reruns
        # (z.B. durch Klick auf Download-Button) weiter sichtbar bleiben.
        if "last_analyse_result" in st.session_state:
            _ar = st.session_state["last_analyse_result"]
            _ir = st.session_state["last_intake_result"]
            st.divider()
            st.markdown("**Ergebnis exportieren:**")
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    label="JSON herunterladen",
                    data=_result_to_json(_ar, _ir),
                    file_name=f"analyse_{_ar.eingabe_checksum[:8]}.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with dl_col2:
                st.download_button(
                    label="CSV herunterladen",
                    data=_result_to_csv(_ar, _ir),
                    file_name=f"analyse_{_ar.eingabe_checksum[:8]}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

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
                    f"P{1000+i}: Fehler in Steuergerät {i % 5} – Sensor außer Bereich"
                    for i in range(50)
                ),
            },
            {
                "label": "QA-Prüfbericht",
                "text": (
                    "Prüfbericht QA-2024-0815\nFahrzeug-FIN: WDB906232N3123456\n"
                    "Prüfdatum: 15.08.2024\nPrüfer: P54321\n"
                    + "\n".join(
                        f"Prüfpunkt {i+1}: {'OK' if i % 3 != 0 else 'NACHARBEIT'} – "
                        f"{'Bremse' if i % 2 == 0 else 'Lenkung'} {i}"
                        for i in range(40)
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
                    + "\n".join(f"Schritt {i+1}: Arbeitsschritt abgeschlossen" for i in range(30))
                ),
            },
            {
                "label": "Historisches Wartungsarchiv (Stress)",
                "text": "\n".join(
                    f"Eintrag {i+1} | Datum: {(i%28)+1:02d}.{(i%12)+1:02d}.202{i%4} | "
                    f"km: {50000 + i*2000} | Maßnahme: Routineinspektion {i%5}"
                    for i in range(200)
                ),
            },
        ]

        with st.spinner("Benchmark läuft …"):
            results = run_benchmark(test_cases)

        c1, c2, c3 = st.columns(3)
        c1.metric("Ø Token-Einsparung", f"{results['avg_token_reduction_pct']:.1f}%")
        c2.metric("Ø Latenz",           f"{results['avg_latency_ms']:.3f} ms")
        c3.metric("Test-Cases",         results["total_cases"])

        st.divider()
        for case in results["cases"]:
            with st.expander(f"📄 {case['label']}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Original",    f"{case['original_tokens']:,} Tokens")
                c2.metric("Komprimiert", f"{case['compressed_tokens']:,} Tokens")
                c3.metric("Einsparung",  f"{case['reduction_pct']:.1f}%")
                c4.metric("Latenz",      f"{case['latency_ms']:.3f} ms")
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
