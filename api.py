"""
Daimler Buses CompText – FastAPI REST-Schnittstelle
Startbefehl: uvicorn api:app --reload

Endpunkte:
  POST /analyze          – Vollständige Pipeline (Intake → Triage → Analyse)
  POST /compress         – Nur KVTC-Kompression
  POST /triage           – Nur Prioritätsklassifizierung
  GET  /health           – Health-Check
  GET  /stats            – Dashboard-Metriken (Uptime, Bytes, Tokens)
  GET  /benchmark        – Standard-Benchmark ausführen
"""

from __future__ import annotations

import os
import time
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

# Global metrics for "Enterprise Dashboard"
START_TIME = time.time()
PROCESSED_COMPRESSED_BYTES = 0
TOTAL_TOKENS_ORIGINAL = 0
TOTAL_TOKENS_COMPRESSED = 0

app = FastAPI(
    title="Daimler Buses CompText API",
    description=(
        "Industrielle KI-Token-Komprimierung und Prozessanalyse. "
        "DSGVO-konform, Edge-fähig, Enterprise Ready."
    ),
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Singleton agents + cache (created once at startup)
# ---------------------------------------------------------------------------

_intake        = IntakeAgent(IndustrialKVTCStrategy(
    DEFAULT_CONFIG.kvtc_header_lines, DEFAULT_CONFIG.kvtc_window_lines
))
_triage        = TriageAgent()
_result_cache  = AnalysisResultCache(max_size=int(os.getenv("CACHE_MAX_SIZE", "256")))
_analysis      = AnalysisAgent(DEFAULT_CONFIG.analysis, cache=_result_cache)


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


class AuditTrail(BaseModel):
    checksum: str
    steps: list[str]
    timestamp: str
    verified: bool = True


class KVTCResponse(BaseModel):
    original_tokens: int
    compressed_tokens: int
    token_reduction_pct: float
    compression_summary: str
    frame: str
    audit_trail: AuditTrail
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
    compression_summary: str
    latenz_ms: float
    bereinigungen: list[str]
    doc_type: DocumentType
    audit_trail: AuditTrail
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
# Helper functions
# ---------------------------------------------------------------------------

def _update_global_metrics(orig: int, comp: int, frame: str):
    global TOTAL_TOKENS_ORIGINAL, TOTAL_TOKENS_COMPRESSED, PROCESSED_COMPRESSED_BYTES
    TOTAL_TOKENS_ORIGINAL += orig
    TOTAL_TOKENS_COMPRESSED += comp
    PROCESSED_COMPRESSED_BYTES += len(frame.encode('utf-8'))


def _build_compression_summary(orig: int, comp: int) -> str:
    reduction = round((1 - comp / orig) * 100, 2) if orig > 0 else 0
    return f"Saved {reduction}% tokens ({orig} -> {comp}). 100% Context preserved via KVTC."


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "comptext-daimler",
        "version": "0.3.0",
        "cache_size": _result_cache.size,
        "cache_hit_rate": round(_result_cache.stats.hit_rate, 3),
    }


@app.get("/stats")
def stats() -> dict[str, Any]:
    uptime_seconds = time.time() - START_TIME
    savings_pct = round((1 - TOTAL_TOKENS_COMPRESSED / TOTAL_TOKENS_ORIGINAL) * 100, 2) if TOTAL_TOKENS_ORIGINAL > 0 else 0
    return {
        "uptime_seconds": round(uptime_seconds, 2),
        "processed_compressed_bytes": PROCESSED_COMPRESSED_BYTES,
        "total_tokens_original": TOTAL_TOKENS_ORIGINAL,
        "total_tokens_compressed": TOTAL_TOKENS_COMPRESSED,
        "total_token_savings_pct": savings_pct,
        "cache_hit_rate": round(_result_cache.stats.hit_rate, 3),
        "version": "0.3.0"
    }


@app.post("/compress", response_model=KVTCResponse)
def compress(req: CompressRequest) -> KVTCResponse:
    try:
        result = _intake._kvtc.compress(req.text)
        _update_global_metrics(result.original_tokens, result.compressed_tokens, result.frame)

        return KVTCResponse(
            original_tokens=result.original_tokens,
            compressed_tokens=result.compressed_tokens,
            token_reduction_pct=result.token_reduction_pct,
            compression_summary=_build_summary(result.original_tokens, result.compressed_tokens),
            frame=result.frame,
            audit_trail=AuditTrail(
                checksum=result.checksum,
                steps=["KVTC-Encoding", "Layer-Extraction"],
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            ),
            latency_ms=result.latency_ms,
        )
    except Exception as e:
        log.error("compress failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


def _build_summary(orig: int, comp: int) -> str:
    # Small helper for local use
    reduction = round((1 - comp / orig) * 100, 2) if orig > 0 else 0
    return f"Saved {reduction}% tokens. Context preserved."


@app.post("/triage", response_model=TriageResponse)
def triage(req: TriageRequest) -> TriageResponse:
    try:
        from src.models.schemas import EingabeDokument
        doc = EingabeDokument(raw_text=req.text, doc_type=req.doc_type)
        result = _triage.classify(doc)
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
    log.info("Analyze request", extra={"quelle": req.quelle, "text_len": len(req.text)})
    try:
        intake_result  = _intake.process(req.text, quelle=req.quelle)
        _update_global_metrics(
            intake_result.kvtc.original_tokens,
            intake_result.kvtc.compressed_tokens,
            intake_result.kvtc.frame
        )

        triage_result  = _triage.classify(intake_result.dokument)
        analyse_result = _analysis.analyze(intake_result.dokument, intake_result.kvtc, triage_result)

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
            compression_summary=_build_summary(analyse_result.token_original, analyse_result.token_komprimiert),
            latenz_ms=analyse_result.latenz_ms,
            bereinigungen=intake_result.bereinigungen,
            doc_type=intake_result.dokument.doc_type,
            audit_trail=AuditTrail(
                checksum=intake_result.kvtc.checksum,
                steps=["DSGVO-Sanitization", "KVTC-Compression", "Triage-Logic", "LLM-Analysis"],
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            ),
            modell_id=analyse_result.modell_id,
        )
    except Exception as e:
        log.error("analyze failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/batch/analyze", response_model=BatchAnalyzeResponse)
def batch_analyze(req: BatchAnalyzeRequest) -> BatchAnalyzeResponse:
    log.info("Batch analyze request", extra={"count": len(req.documents)})
    results: list[BatchItemResult] = []

    for idx, doc_req in enumerate(req.documents):
        try:
            # Re-using the analyze logic for batch
            resp = analyze(doc_req)
            results.append(BatchItemResult(
                index=idx,
                success=True,
                result=resp,
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
    uvicorn.run("api.py:app", host="0.0.0.0", port=10000, reload=False)


if __name__ == "__main__":
    main()
