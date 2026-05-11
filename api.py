"""
Daimler Buses CompText – FastAPI REST-Schnittstelle  v0.3.0
Startbefehl: uvicorn api:app --reload

Endpunkte (Standard):
  POST /analyze              – Vollständige Pipeline (Intake → Triage → Analyse)
  POST /compress             – Nur KVTC-Kompression
  POST /triage               – Nur Prioritätsklassifizierung
  GET  /health               – Health-Check
  GET  /stats                – Dashboard-Metriken
  GET  /benchmark            – Standard-Benchmark

Industrielle Showcase-Endpunkte (n8n-kompatibel):
  POST /api/xentry/optimize       – Diagnostic Log Compression (Xentry)
  POST /api/mo360/filter          – Production Shift Filtering (MO360)
  POST /v1/dedup/supply-chain    – Semantic Deduplication (Supply Chain)
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Showcase modules (root-level scripts – add parent to sys.path)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config import DEFAULT_CONFIG
from showcase.mo360_shift_filter import extract_deviations, get_sample_shift_report
from showcase.supply_chain_dedup import semantic_dedup
from showcase.xentry_optimizer import filter_log, generate_xentry_log
from src.agents.analysis_agent import AnalysisAgent
from src.agents.intake_agent import IntakeAgent
from src.agents.triage_agent import TriageAgent
from src.core.kvtc import IndustrialKVTCStrategy, run_benchmark
from src.core.kvtc_v7_strategy import KVTCV7Strategy
from src.core.result_cache import AnalysisResultCache
from src.models.schemas import DocumentType, ProcessPriority
from src.telemetry import tracker
from src.utils.logging import get_logger

log = get_logger("comptext.api")

START_TIME = time.time()
PROCESSED_COMPRESSED_BYTES = 0
DEFAULT_ALLOWED_ORIGINS = (
    "https://comptext-daimler-api.onrender.com,"
    "https://comptext-daimler-api-jules.onrender.com,"
    "http://localhost:5173,"
    "http://localhost:3000"
)
DEFAULT_ALLOWED_ORIGIN_REGEX = r"https://.*\.vercel\.app"

app = FastAPI(
    title="Daimler Buses CompText API",
    description=(
        "Industrielle KI-Token-Komprimierung und Prozessanalyse. "
        "DSGVO-konform, Edge-fähig. v0.3.0 – Industrial Showcase."
    ),
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Any, exc: RequestValidationError) -> JSONResponse:
    # Strip raw input values from validation errors to prevent PII leaks
    safe_errors = [{"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": safe_errors})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",") if origin.strip()],
    allow_origin_regex=os.getenv("ALLOWED_ORIGIN_REGEX", DEFAULT_ALLOWED_ORIGIN_REGEX),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ---------------------------------------------------------------------------
# Singleton agents + cache
# ---------------------------------------------------------------------------

_strategy = IndustrialKVTCStrategy(DEFAULT_CONFIG.kvtc_header_lines, DEFAULT_CONFIG.kvtc_window_lines)
_v7_strategy = KVTCV7Strategy()
_intake = IntakeAgent(_strategy)
_triage = TriageAgent()
_result_cache = AnalysisResultCache(max_size=int(os.getenv("CACHE_MAX_SIZE", "256")))
_analysis = AnalysisAgent(DEFAULT_CONFIG.analysis, cache=_result_cache)


# ---------------------------------------------------------------------------
# n8n Standard Response Schema
# {"status": "success", "data": {...}, "metrics": {"original": int, "compressed": int, "savings": float}}
# ---------------------------------------------------------------------------


def _n8n_success(data: dict[str, Any], original: int, compressed: int) -> dict[str, Any]:
    import base64

    savings = round((1 - compressed / original) * 100, 4) if original > 0 else 0.0
    next_cursor = base64.b64encode(b"end_of_data").decode("utf-8")
    return {
        "status": "success",
        "data": data,
        "nextCursor": next_cursor,
        "metrics": {
            "original": original,
            "compressed": compressed,
            "savings": savings,
        },
    }


def _n8n_error(code: str, detail: str, recovery_hint: str = "") -> dict[str, Any]:
    """Structured error object that n8n can parse to trigger a Recovery Workflow."""
    return {
        "status": "error",
        "error_code": code,
        "detail": detail,
        "recovery_hint": recovery_hint or "Trigger Recovery Workflow via n8n Error Branch",
        "data": None,
        "metrics": {"original": 0, "compressed": 0, "savings": 0.0},
    }


# ---------------------------------------------------------------------------
# Standard Request/Response models
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    quelle: str = Field(default="API")


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
    documents: list[AnalyzeRequest] = Field(..., min_length=1, max_length=10)


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
# Industrial Showcase Request models
# ---------------------------------------------------------------------------


class XentryRequest(BaseModel):
    log_text: str | None = Field(
        default=None,
        description="Raw Xentry log. If omitted, a synthetic log is generated.",
    )
    log_lines: int = Field(default=500, ge=100, le=10000)
    debug: bool = Field(default=False)


class MO360Request(BaseModel):
    shift_report: str | None = Field(
        default=None,
        description="Raw MO360 shift report. If omitted, sample data is used.",
    )
    debug: bool = Field(default=False)


class SupplyChainRequest(BaseModel):
    updates: list[str] | None = Field(default=None, description="List of supply-chain update strings.")
    debug: bool = Field(default=False)


# ---------------------------------------------------------------------------
# Helpers
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



def _synthetic_benchmark_cases() -> list[dict[str, str]]:
    return [
        {
            "label": "Synthetic maintenance note",
            "text": "Wartungsauftrag SYN-001\nKilometerstand: 80000\nFehlercode: P0300\nStatus: INFO geprüft",
        },
        {
            "label": "Synthetic diagnostic log",
            "text": "\n".join(
                [
                    "2026-05-11T08:00:00 INFO bus=demo line=42 event=start",
                    "2026-05-11T08:01:00 WARN sensor=temp value=91",
                    "2026-05-11T08:02:00 ERROR code=P0300 module=engine",
                    "2026-05-11T08:03:00 INFO action=synthetic-reset",
                ]
            ),
        },
        {
            "label": "Synthetic QA checklist",
            "text": "\n".join(f"Prüfpunkt {i}: OK value={i}" for i in range(30)),
        },
        {
            "label": "Very short synthetic note",
            "text": "OK",
        },
    ]


def _v7_caveat(case_text: str, result_metadata: dict[str, Any]) -> tuple[str, str]:
    event_count = int(result_metadata.get("event_count", 0))
    signals = result_metadata.get("signals", {}) if isinstance(result_metadata.get("signals"), dict) else {}
    if len(case_text) < 16:
        return "warn", "Very short input may favor a V7 micro-frame for metadata safety over token reduction."
    if event_count <= 1:
        return "warn", "Low event coverage; use longer structured synthetic logs for representative comparison."
    if not any(signals.get(key, 0) for key in ("obd_codes", "key_values", "timestamps")):
        return "warn", "Low structured-signal coverage; compression evidence is conservative."
    return "pass", "Synthetic benchmark only; compare trends rather than production claims."


# ---------------------------------------------------------------------------
# Standard Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "comptext-daimler",
        "version": "0.3.0",
        "cache_size": _result_cache.size,
        "cache_hit_rate": round(_result_cache.stats.hit_rate, 3),
        "telemetry_active": bool(os.getenv("TINYBIRD_TOKEN")),
    }


@app.get("/stats")
def stats() -> dict[str, Any]:
    return {
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "processed_compressed_bytes": PROCESSED_COMPRESSED_BYTES,
        "cache_hit_rate": round(_result_cache.stats.hit_rate, 3),
        "version": "0.3.0",
    }


@app.post("/compress", response_model=KVTCResponse)
def compress(req: CompressRequest) -> KVTCResponse:
    global PROCESSED_COMPRESSED_BYTES
    try:
        result = _intake._kvtc.compress(req.text)
        PROCESSED_COMPRESSED_BYTES += len(result.frame.encode("utf-8"))
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


@app.post("/compress/v7", response_model=KVTCResponse)
def compress_v7(req: CompressRequest) -> KVTCResponse:
    global PROCESSED_COMPRESSED_BYTES
    try:
        result = _v7_strategy.compress(req.text)
        PROCESSED_COMPRESSED_BYTES += len(result.frame.encode("utf-8"))
        return KVTCResponse(
            original_tokens=result.original_tokens,
            compressed_tokens=result.compressed_tokens,
            token_reduction_pct=result.token_reduction_pct,
            frame=result.frame,
            checksum=result.checksum,
            latency_ms=result.latency_ms,
        )
    except Exception as e:
        log.error("compress v7 failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


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
    global PROCESSED_COMPRESSED_BYTES
    log.info("Analyze request", extra={"quelle": req.quelle, "text_len": len(req.text)})
    try:
        intake_result = _intake.process(req.text, quelle=req.quelle)
        PROCESSED_COMPRESSED_BYTES += len(intake_result.kvtc.frame.encode("utf-8"))
        triage_result = _triage.classify(intake_result.dokument)
        analyse_result = _analysis.analyze(intake_result.dokument, intake_result.kvtc, triage_result)
        return _build_analyze_response(intake_result, analyse_result)
    except Exception as e:
        log.error("analyze failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/batch/analyze", response_model=BatchAnalyzeResponse)
def batch_analyze(req: BatchAnalyzeRequest) -> BatchAnalyzeResponse:
    global PROCESSED_COMPRESSED_BYTES
    log.info("Batch analyze request", extra={"count": len(req.documents)})
    results: list[BatchItemResult] = []
    for idx, doc_req in enumerate(req.documents):
        try:
            intake_result = _intake.process(doc_req.text, quelle=doc_req.quelle)
            PROCESSED_COMPRESSED_BYTES += len(intake_result.kvtc.frame.encode("utf-8"))
            triage_result = _triage.classify(intake_result.dokument)
            analyse_result = _analysis.analyze(intake_result.dokument, intake_result.kvtc, triage_result)
            results.append(
                BatchItemResult(
                    index=idx,
                    success=True,
                    result=_build_analyze_response(intake_result, analyse_result),
                )
            )
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
    return run_benchmark(_synthetic_benchmark_cases()[:3])


@app.get("/benchmark/v7")
def benchmark_v7() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for case in _synthetic_benchmark_cases():
        result = _v7_strategy.compress(case["text"], context_metadata={"label": case["label"]})
        frame_meta = result.zones.get("v7", {}) if isinstance(result.zones, dict) else {}
        results.append(
            {
                "label": case["label"],
                "original_tokens": result.original_tokens,
                "compressed_tokens": result.compressed_tokens,
                "reduction_pct": result.token_reduction_pct,
                "latency_ms": result.latency_ms,
                "checksum": result.checksum,
                "v7_frame_type": result.metadata.get("frame_type"),
                "v7_event_count": result.metadata.get("event_count"),
                "v7_severity_counts": result.metadata.get("severity_counts", {}),
                "v7_signals": frame_meta.get("signals", {}),
            }
        )
    count = len(results)
    return {
        "cases": results,
        "avg_token_reduction_pct": round(sum(r["reduction_pct"] for r in results) / count, 2) if count else 0,
        "avg_latency_ms": round(sum(r["latency_ms"] for r in results) / count, 3) if count else 0,
        "total_cases": count,
        "data_policy": "synthetic-only",
    }


@app.get("/benchmark/compare")
def benchmark_compare() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    industrial = IndustrialKVTCStrategy(DEFAULT_CONFIG.kvtc_header_lines, DEFAULT_CONFIG.kvtc_window_lines)
    for case in _synthetic_benchmark_cases():
        industrial_result = industrial.compress(case["text"], context_metadata={"label": case["label"]})
        v7_result = _v7_strategy.compress(case["text"], context_metadata={"label": case["label"]})
        frame_meta = v7_result.zones.get("v7", {}) if isinstance(v7_result.zones, dict) else {}
        decision, caveat = _v7_caveat(case["text"], {**v7_result.metadata, **frame_meta})
        cases.append(
            {
                "label": case["label"],
                "industrial_original_tokens": industrial_result.original_tokens,
                "industrial_compressed_tokens": industrial_result.compressed_tokens,
                "industrial_reduction_pct": industrial_result.token_reduction_pct,
                "v7_original_tokens": v7_result.original_tokens,
                "v7_compressed_tokens": v7_result.compressed_tokens,
                "v7_reduction_pct": v7_result.token_reduction_pct,
                "delta_reduction_pct": round(v7_result.token_reduction_pct - industrial_result.token_reduction_pct, 2),
                "v7_frame_type": v7_result.metadata.get("frame_type"),
                "v7_event_count": v7_result.metadata.get("event_count"),
                "v7_severity_counts": v7_result.metadata.get("severity_counts", {}),
                "decision": decision,
                "caveat": caveat,
            }
        )
    return {
        "cases": cases,
        "data_policy": "synthetic-only",
        "caveat": "Benchmarks use deterministic synthetic fixtures and do not prove production Daimler performance.",
    }


# ---------------------------------------------------------------------------
# INDUSTRIAL SHOWCASE ENDPOINTS – n8n kompatibel
# ---------------------------------------------------------------------------


@app.post("/v1/optimize/xentry")
def optimize_xentry(req: XentryRequest) -> dict[str, Any]:
    """
    Xentry Diagnostic Log Compression.
    Filtert relevante Ereignisse, komprimiert via KVTC.
    n8n Response: {"status","data","metrics"}
    """
    global PROCESSED_COMPRESSED_BYTES
    t0 = time.perf_counter()
    try:
        raw_log = req.log_text if req.log_text else generate_xentry_log(req.log_lines)

        filtered = filter_log(raw_log)
        if not filtered.strip():
            filtered = "[NO_CRITICAL_EVENTS]"

        result = _strategy.compress(filtered)
        orig_tokens = _strategy.estimate_tokens(raw_log)
        comp_tokens = result.compressed_tokens
        savings = round((1 - comp_tokens / orig_tokens) * 100, 4) if orig_tokens > 0 else 0.0
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        PROCESSED_COMPRESSED_BYTES += len(result.frame.encode("utf-8"))

        tb_queued = tracker.track(
            endpoint="xentry",
            original_tokens=orig_tokens,
            compressed_tokens=comp_tokens,
            savings_percentage=savings,
            latency_ms=latency_ms,
            extra={"scenario": "xentry_diagnostic"},
        )

        data = {
            "scenario": "xentry_diagnostic_compression",
            "raw_lines": len(raw_log.splitlines()),
            "filtered_lines": len(filtered.splitlines()),
            "kvtc_frame": result.frame,
            "checksum": result.checksum,
            "latency_ms": latency_ms,
        }
        if req.debug:
            data["tinybird_queued"] = tb_queued

        return _n8n_success(data, orig_tokens, comp_tokens)

    except Exception as exc:
        log.error("xentry endpoint failed", extra={"error": str(exc)}, exc_info=True)
        return _n8n_error(
            code="XENTRY_PROCESSING_ERROR",
            detail="Internal processing error.",
            recovery_hint="Check log_text format. Trigger n8n Recovery Workflow: xentry-fallback.",
        )


@app.post("/v1/filter/mo360")
def filter_mo360(req: MO360Request) -> dict[str, Any]:
    """
    MO360 Production Shift Report Filtering.
    Extrahiert Abweichungen, komprimiert via KVTC.
    n8n Response: {"status","data","metrics"}
    """
    global PROCESSED_COMPRESSED_BYTES
    t0 = time.perf_counter()
    try:
        raw_report = req.shift_report if req.shift_report else get_sample_shift_report()

        structured = extract_deviations(raw_report)
        if not structured.strip():
            structured = "[NO_DEVIATIONS_DETECTED]"

        result = _strategy.compress(structured)
        orig_tokens = _strategy.estimate_tokens(raw_report)
        comp_tokens = result.compressed_tokens
        savings = round((1 - comp_tokens / orig_tokens) * 100, 4) if orig_tokens > 0 else 0.0
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        PROCESSED_COMPRESSED_BYTES += len(result.frame.encode("utf-8"))

        tb_queued = tracker.track(
            endpoint="mo360",
            original_tokens=orig_tokens,
            compressed_tokens=comp_tokens,
            savings_percentage=savings,
            latency_ms=latency_ms,
            extra={"scenario": "mo360_shift_filter"},
        )

        data = {
            "scenario": "mo360_shift_filter",
            "structured_report": structured,
            "kvtc_frame": result.frame,
            "checksum": result.checksum,
            "latency_ms": latency_ms,
        }
        if req.debug:
            data["tinybird_queued"] = tb_queued

        return _n8n_success(data, orig_tokens, comp_tokens)

    except Exception as exc:
        log.error("mo360 endpoint failed", extra={"error": str(exc)}, exc_info=True)
        return _n8n_error(
            code="MO360_PROCESSING_ERROR",
            detail="Internal processing error.",
            recovery_hint="Check shift_report format. Trigger n8n Recovery Workflow: mo360-fallback.",
        )


@app.post("/v1/dedup/supply-chain")
def dedup_supply_chain(req: SupplyChainRequest) -> dict[str, Any]:
    """
    Supply Chain Semantic Deduplication.
    Dedupliziert Lieferanten-Updates, komprimiert via KVTC.
    n8n Response: {"status","data","metrics"}
    """
    global PROCESSED_COMPRESSED_BYTES
    t0 = time.perf_counter()
    try:
        from showcase.supply_chain_dedup import get_supplier_updates

        updates = req.updates if req.updates else get_supplier_updates()
        raw_text = "\n".join(updates)

        deduped = semantic_dedup(updates)
        dedup_text = "\n".join(deduped)

        result = _strategy.compress(dedup_text)
        orig_tokens = _strategy.estimate_tokens(raw_text)
        comp_tokens = result.compressed_tokens
        savings = round((1 - comp_tokens / orig_tokens) * 100, 4) if orig_tokens > 0 else 0.0
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        PROCESSED_COMPRESSED_BYTES += len(result.frame.encode("utf-8"))

        tb_queued = tracker.track(
            endpoint="supply-chain",
            original_tokens=orig_tokens,
            compressed_tokens=comp_tokens,
            savings_percentage=savings,
            latency_ms=latency_ms,
            extra={"scenario": "supply_chain_dedup"},
        )

        data = {
            "scenario": "supply_chain_deduplication",
            "total_updates": len(updates),
            "unique_updates": len(deduped),
            "duplicates_removed": len(updates) - len(deduped),
            "deduplicated_text": dedup_text,
            "kvtc_frame": result.frame,
            "checksum": result.checksum,
            "latency_ms": latency_ms,
        }
        if req.debug:
            data["tinybird_queued"] = tb_queued

        return _n8n_success(data, orig_tokens, comp_tokens)

    except Exception as exc:
        log.error("supply-chain endpoint failed", extra={"error": str(exc)}, exc_info=True)
        return _n8n_error(
            code="SUPPLY_CHAIN_PROCESSING_ERROR",
            detail="Internal processing error.",
            recovery_hint="Check updates list format. Trigger n8n Recovery Workflow: supply-chain-fallback.",
        )


# ---------------------------------------------------------------------------
# /api/ route aliases (React frontend convention)
# ---------------------------------------------------------------------------

app.post("/v1/optimize/xentry")(optimize_xentry)
app.post("/v1/filter/mo360")(filter_mo360)
app.post("/api/supply-chain/dedup")(dedup_supply_chain)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
