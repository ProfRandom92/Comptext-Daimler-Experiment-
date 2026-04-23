"""
Daimler Buses CompText – FastAPI REST-Schnittstelle
Startbefehl: uvicorn api:app --reload

Endpunkte:
  POST /analyze          – Vollständige Pipeline (Intake → Triage → Analyse)
  POST /compress         – Nur KVTC-Kompression
  POST /triage           – Nur Prioritätsklassifizierung
  GET  /health           – Health-Check
  GET  /benchmark        – Standard-Benchmark ausführen
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import DEFAULT_CONFIG
from src.agents.analysis_agent import AnalysisAgent
from src.agents.intake_agent import IntakeAgent
from src.agents.triage_agent import TriageAgent
from src.core.kvtc import IndustrialKVTCStrategy, run_benchmark
from src.core.result_cache import AnalysisResultCache
from src.models.schemas import DocumentType, ProcessPriority
from src.utils.logging import get_logger

log = get_logger("comptext.api")

# ---------------------------------------------------------------------------
# CORS: restrict to known origins via env var (CORS_ORIGINS=http://a,http://b)
# ---------------------------------------------------------------------------
_cors_origins_raw = os.getenv("CORS_ORIGINS", "")
_allowed_origins: list[str] = (
    [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
    if _cors_origins_raw
    else []
)

# ---------------------------------------------------------------------------
# Singleton agents + cache – initialised lazily at startup
# ---------------------------------------------------------------------------
_intake: IntakeAgent | None = None
_triage: TriageAgent | None = None
_result_cache: AnalysisResultCache | None = None
_analysis: AnalysisAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _intake, _triage, _result_cache, _analysis
    try:
        _result_cache = AnalysisResultCache(
            max_size=int(os.getenv("CACHE_MAX_SIZE", "256")),
            ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "3600")),
        )
        _intake   = IntakeAgent(IndustrialKVTCStrategy(
            DEFAULT_CONFIG.kvtc_header_lines, DEFAULT_CONFIG.kvtc_window_lines,
        ))
        _triage   = TriageAgent()
        _analysis = AnalysisAgent(DEFAULT_CONFIG.analysis, cache=_result_cache)
        log.info("Agents initialised", extra={"backend": DEFAULT_CONFIG.analysis.backend})
    except Exception:
        log.critical("Agent initialisation failed – API will return 503", exc_info=True)
    yield


app = FastAPI(
    title="Daimler Buses CompText API",
    description=(
        "Industrielle KI-Token-Komprimierung und Prozessanalyse. "
        "DSGVO-konform, Edge-fähig."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=bool(_allowed_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


def _require_agents() -> tuple[IntakeAgent, TriageAgent, AnalysisAgent]:
    if _intake is None or _triage is None or _analysis is None:
        raise HTTPException(status_code=503, detail="Service nicht verfügbar – Agent-Initialisierung fehlgeschlagen")
    return _intake, _triage, _analysis


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Roher Dokumenttext")
    quelle: str = Field(default="API", description="Quellsystem (z.B. SAP, MES)")


class CompressRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TriageRequest(BaseModel):
    text: str = Field(..., min_length=1)
    doc_type: DocumentType = DocumentType.FREITEXT


class KVTCResponse(BaseModel):
    original_tokens: int
    compressed_tokens: int
    token_reduction_pct: float
    frame: str
    checksum: str
    latency_ms: float


class TriageResponse(BaseModel):
    prioritaet: ProcessPriority
    begruendung: str
    ausgeloeste_regeln: list[str]
    eskalations_hinweis: str


class AnalyzeResponse(BaseModel):
    eingabe_checksum: str
    prioritaet: ProcessPriority
    zusammenfassung: str
    massnahmen: list[str]
    erkannte_fehlercodes: list[str]
    konfidenz: float
    token_original: int
    token_komprimiert: int
    token_einsparung_pct: float
    latenz_ms: float
    bereinigungen: list[str]
    doc_type: DocumentType
    modell_id: str


class BatchAnalyzeRequest(BaseModel):
    documents: list[AnalyzeRequest] = Field(
        ..., min_length=1, max_length=10, description="Liste von Dokumenten (max. 10)"
    )


class BatchItemResult(BaseModel):
    index: int
    success: bool
    result: AnalyzeResponse | None = None
    error: str | None = None


class BatchAnalyzeResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[BatchItemResult]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _build_analyze_response(intake_result: Any, analyse_result: Any) -> AnalyzeResponse:
    return AnalyzeResponse(
        eingabe_checksum=analyse_result.eingabe_checksum,
        prioritaet=analyse_result.prioritaet,
        zusammenfassung=analyse_result.zusammenfassung,
        massnahmen=analyse_result.massnahmen,
        erkannte_fehlercodes=analyse_result.erkannte_fehlercodes,
        konfidenz=analyse_result.konfidenz,
        token_original=analyse_result.token_original,
        token_komprimiert=analyse_result.token_komprimiert,
        token_einsparung_pct=analyse_result.token_einsparung_pct,
        latenz_ms=analyse_result.latenz_ms,
        bereinigungen=intake_result.bereinigungen,
        doc_type=intake_result.dokument.doc_type,
        modell_id=analyse_result.modell_id,
    )


@app.get("/health")
def health() -> dict[str, Any]:
    ready = _intake is not None
    return {
        "status": "ok" if ready else "degraded",
        "service": "comptext-daimler",
        "version": "0.2.0",
        "cache_size": _result_cache.size if _result_cache else 0,
        "cache_hit_rate": round(_result_cache.stats.hit_rate, 3) if _result_cache else 0.0,
    }


@app.post("/compress", response_model=KVTCResponse)
def compress(req: CompressRequest) -> KVTCResponse:
    intake, _, _ = _require_agents()
    try:
        result = intake._kvtc.compress(req.text)
        return KVTCResponse(
            original_tokens=result.original_tokens,
            compressed_tokens=result.compressed_tokens,
            token_reduction_pct=result.token_reduction_pct,
            frame=result.frame,
            checksum=result.checksum,
            latency_ms=result.latency_ms,
        )
    except Exception as e:
        log.error("compress failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/triage", response_model=TriageResponse)
def triage(req: TriageRequest) -> TriageResponse:
    _, triage_agent, _ = _require_agents()
    try:
        from src.models.schemas import EingabeDokument
        doc = EingabeDokument(raw_text=req.text, doc_type=req.doc_type)
        result = triage_agent.classify(doc)
        return TriageResponse(
            prioritaet=result.prioritaet,
            begruendung=result.begruendung,
            ausgeloeste_regeln=result.ausgeloeste_regeln,
            eskalations_hinweis=result.eskalations_hinweis,
        )
    except Exception as e:
        log.error("triage failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    intake, triage_agent, analysis_agent = _require_agents()
    log.info("Analyze request", extra={"quelle": req.quelle, "text_len": len(req.text)})
    try:
        intake_result  = intake.process(req.text, quelle=req.quelle)
        triage_result  = triage_agent.classify(intake_result.dokument)
        analyse_result = analysis_agent.analyze(intake_result.dokument, intake_result.kvtc, triage_result)
        return _build_analyze_response(intake_result, analyse_result)
    except Exception as e:
        log.error("analyze failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/batch/analyze", response_model=BatchAnalyzeResponse)
def batch_analyze(req: BatchAnalyzeRequest) -> BatchAnalyzeResponse:
    """Verarbeitet bis zu 10 Dokumente sequenziell. Fehler in einzelnen Dokumenten
    stoppen nicht die Verarbeitung der übrigen."""
    intake, triage_agent, analysis_agent = _require_agents()
    log.info("Batch analyze request", extra={"count": len(req.documents)})
    results: list[BatchItemResult] = []

    for idx, doc_req in enumerate(req.documents):
        try:
            intake_result  = intake.process(doc_req.text, quelle=doc_req.quelle)
            triage_result  = triage_agent.classify(intake_result.dokument)
            analyse_result = analysis_agent.analyze(
                intake_result.dokument, intake_result.kvtc, triage_result
            )
            results.append(BatchItemResult(
                index=idx,
                success=True,
                result=_build_analyze_response(intake_result, analyse_result),
            ))
        except Exception as e:
            log.error("batch item failed", extra={"index": idx, "error": str(e)})
            results.append(BatchItemResult(index=idx, success=False, error=str(e)))

    succeeded = sum(1 for r in results if r.success)
    return BatchAnalyzeResponse(
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )


@app.get("/benchmark")
def benchmark() -> dict[str, Any]:
    cases = [
        {"label": "Wartungsprotokoll",  "text": "Wartungsauftrag 001\nKilometerstand: 80000\nFehlercode: P0300"},
        {"label": "OBD Fehlerspeicher", "text": "\n".join(f"P{1000+i}: Sensor {i}" for i in range(20))},
        {"label": "QA Prüfbericht",     "text": "\n".join(f"Prüfpunkt {i}: OK" for i in range(30))},
    ]
    return run_benchmark(cases)


def main() -> None:
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
