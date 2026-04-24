"""
Daimler Dashboard FastAPI Backend
Integrates CompText MCP Server with clinical FHIR processing and visualization.

API Endpoints:
- POST /api/pipeline/process      Process FHIR bundle via CompText
- GET  /api/scenarios             List available clinical scenarios
- POST /api/benchmark             Run performance benchmarks
- GET  /api/benchmark/results/{id} Retrieve benchmark results
- POST /api/validate              Validate CompText frame
- GET  /health                    Health check
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
import uuid
import os
from datetime import datetime
import asyncio
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class FHIRBundle(BaseModel):
    """FHIR R4 Bundle"""
    resourceType: str = "Bundle"
    type: str = "transaction"
    entry: List[Dict[str, Any]] = []

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": []
            }
        }


class PipelineRequest(BaseModel):
    """Pipeline processing request"""
    bundle: Optional[FHIRBundle] = None
    scenario: Optional[str] = Field(None, description="Built-in scenario: STEMI, SEPSIS, STROKE, ANAPHYLAXIE, DM_HYPO")
    include_benchmark: bool = Field(False, description="Include token metrics in response")

    class Config:
        schema_extra = {
            "example": {
                "scenario": "STEMI",
                "include_benchmark": True
            }
        }


class PipelineResponse(BaseModel):
    """Pipeline processing response"""
    id: str
    scenario: str
    frame: str
    metrics: Dict[str, Any]
    safety: Dict[str, Any]
    timestamp: datetime

    class Config:
        schema_extra = {
            "example": {
                "id": "proc-123456",
                "scenario": "STEMI",
                "frame": "CT:v5 SC:STEMI TRI:P1\nVS[hr:118 sbp:82 spo2:91]\n...",
                "metrics": {
                    "reduction_pct": 93.9,
                    "tokens_input": 1847,
                    "tokens_final": 112
                },
                "safety": {
                    "allergies_preserved": 1,
                    "medications_preserved": 1,
                    "triage_accurate": "P1"
                },
                "timestamp": "2026-04-23T12:00:00Z"
            }
        }


class BenchmarkRequest(BaseModel):
    """Benchmark request"""
    scenarios: List[str] = Field(["ALL"], description="Scenarios to benchmark")
    detailed: bool = Field(False, description="Include stage-by-stage metrics")

    class Config:
        schema_extra = {
            "example": {
                "scenarios": ["STEMI", "SEPSIS", "STROKE"],
                "detailed": True
            }
        }


class ValidationRequest(BaseModel):
    """Frame validation request"""
    frame: str
    checks: List[str] = Field(["syntax", "safety", "gdpr"], description="Checks to run")


class ValidationResponse(BaseModel):
    """Frame validation response"""
    valid: bool
    checks: Dict[str, Any]
    issues: List[str] = []


class ScenarioInfo(BaseModel):
    """Clinical scenario information"""
    id: str
    name: str
    icd10: List[str]
    triage: str
    estimated_tokens: int


class HealthStatus(BaseModel):
    """Health check response"""
    status: str
    mcp_connected: bool
    services: Dict[str, str]
    timestamp: datetime


# ============================================================================
# MCP CLIENT WRAPPER
# ============================================================================

class MCPClient:
    """Wrapper for CompText MCP Server communication"""

    def __init__(self, mcp_url: str = "http://localhost:3000"):
        self.mcp_url = mcp_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.connected = False

    async def health_check(self) -> bool:
        """Check MCP server health"""
        try:
            response = await self.client.get(f"{self.mcp_url}/health")
            self.connected = response.status_code == 200
            return self.connected
        except Exception as e:
            logger.error(f"MCP health check failed: {e}")
            self.connected = False
            return False

    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool"""
        try:
            response = await self.client.post(
                f"{self.mcp_url}/tools/{tool_name}",
                json=args
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"MCP tool call failed: {tool_name}: {e}")
            raise

    async def pipeline(self, bundle: Optional[Dict] = None, scenario: Optional[str] = None) -> Dict:
        """Run CompText pipeline"""
        args = {}
        if bundle:
            args["bundle"] = bundle
        if scenario:
            args["scenario"] = scenario
        return await self.call_tool("comptext_pipeline", args)

    async def benchmark(self, scenarios: List[str], detailed: bool = False) -> Dict:
        """Run benchmarks"""
        args = {
            "scenarios": scenarios if scenarios != ["ALL"] else None,
            "detailed": detailed
        }
        return await self.call_tool("comptext_benchmark", {k: v for k, v in args.items() if v is not None})

    async def scenarios(self, filter: str = "all") -> Dict:
        """List scenarios"""
        return await self.call_tool("comptext_scenarios", {"filter": filter})

    async def validate(self, frame: str, checks: List[str]) -> Dict:
        """Validate frame"""
        return await self.call_tool("comptext_validate", {"frame": frame, "checks": checks})


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="CompText Daimler Dashboard API",
    description="Clinical FHIR processing via CompText pipeline",
    version="1.0.0"
)

# Add CORS middleware – restrict to explicit origins; wildcard + credentials violates CORS spec
_CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Initialize MCP client
mcp_url = os.getenv("COMPTEXT_MCP_URL", "http://localhost:3000")
mcp_client = MCPClient(mcp_url)

# In-memory storage for results (use database in production)
results_store: Dict[str, PipelineResponse] = {}
benchmark_store: Dict[str, Dict] = {}


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    logger.info("Daimler Dashboard starting...")
    mcp_connected = await mcp_client.health_check()
    logger.info(f"MCP Server connection: {'✓ Connected' if mcp_connected else '✗ Failed'}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await mcp_client.client.aclose()


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    is_connected = await mcp_client.health_check()

    return HealthStatus(
        status="healthy" if is_connected else "degraded",
        mcp_connected=is_connected,
        services={
            "mcp_server": "connected" if is_connected else "unreachable",
            "api": "operational",
            "database": "connected"
        },
        timestamp=datetime.utcnow()
    )


# ============================================================================
# PIPELINE ENDPOINTS
# ============================================================================

@app.post("/api/pipeline/process", response_model=PipelineResponse)
async def process_pipeline(request: PipelineRequest):
    """Process FHIR bundle through CompText pipeline"""
    try:
        # Call MCP server
        mcp_result = await mcp_client.pipeline(
            bundle=request.bundle.dict() if request.bundle else None,
            scenario=request.scenario
        )

        # Handle errors from MCP
        if "error" in mcp_result:
            raise HTTPException(status_code=400, detail=mcp_result.get("error"))

        # Create response
        process_id = str(uuid.uuid4())[:8]
        response = PipelineResponse(
            id=f"proc-{process_id}",
            scenario=mcp_result.get("scenario", request.scenario or "STEMI"),
            frame=mcp_result.get("frame", ""),
            metrics=mcp_result.get("metrics", {}),
            safety=mcp_result.get("safety", {}),
            timestamp=datetime.utcnow()
        )

        # Store result
        results_store[response.id] = response

        logger.info(f"Pipeline processed: {response.id} ({response.scenario})")
        return response

    except Exception as e:
        logger.error(f"Pipeline processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipeline/upload")
async def upload_fhir_bundle(file: UploadFile = File(...)):
    """Upload FHIR bundle JSON file"""
    try:
        content = await file.read()
        bundle = json.loads(content)

        # Validate FHIR structure
        if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
            raise ValueError("Invalid FHIR Bundle")

        # Process through pipeline
        request = PipelineRequest(bundle=FHIRBundle(**bundle))
        return await process_pipeline(request)

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid FHIR: {e}")


@app.get("/api/pipeline/results/{process_id}", response_model=PipelineResponse)
async def get_result(process_id: str):
    """Retrieve pipeline result"""
    if process_id not in results_store:
        raise HTTPException(status_code=404, detail=f"Result not found: {process_id}")

    return results_store[process_id]


# ============================================================================
# SCENARIOS ENDPOINTS
# ============================================================================

@app.get("/api/scenarios", response_model=Dict[str, Any])
async def list_scenarios(filter: str = "all"):
    """List available clinical scenarios"""
    try:
        result = await mcp_client.scenarios(filter=filter)
        return result
    except Exception as e:
        logger.error(f"Failed to list scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scenarios/{scenario_id}/process", response_model=PipelineResponse)
async def process_scenario(scenario_id: str):
    """Process pre-built scenario"""
    try:
        return await process_pipeline(PipelineRequest(scenario=scenario_id))
    except Exception as e:
        logger.error(f"Scenario processing failed: {scenario_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BENCHMARK ENDPOINTS
# ============================================================================

@app.post("/api/benchmark")
async def run_benchmark(request: BenchmarkRequest, background_tasks: BackgroundTasks):
    """Run benchmarks on specified scenarios"""
    try:
        benchmark_id = str(uuid.uuid4())[:8]

        # Run in background
        async def execute_benchmark():
            try:
                result = await mcp_client.benchmark(
                    scenarios=request.scenarios,
                    detailed=request.detailed
                )
                benchmark_store[benchmark_id] = {
                    "id": benchmark_id,
                    "status": "completed",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.info(f"Benchmark completed: {benchmark_id}")
            except Exception as e:
                benchmark_store[benchmark_id] = {
                    "id": benchmark_id,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }

        background_tasks.add_task(execute_benchmark)

        return {
            "benchmark_id": benchmark_id,
            "status": "started",
            "poll_url": f"/api/benchmark/results/{benchmark_id}",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Benchmark start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/benchmark/results/{benchmark_id}")
async def get_benchmark_results(benchmark_id: str):
    """Get benchmark results"""
    if benchmark_id not in benchmark_store:
        raise HTTPException(status_code=404, detail=f"Benchmark not found: {benchmark_id}")

    return benchmark_store[benchmark_id]


# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================

@app.post("/api/validate", response_model=ValidationResponse)
async def validate_frame(request: ValidationRequest):
    """Validate CompText frame"""
    try:
        result = await mcp_client.validate(
            frame=request.frame,
            checks=request.checks
        )

        return ValidationResponse(
            valid=result.get("frame_valid", False),
            checks=result.get("checks", {}),
            issues=[] if result.get("frame_valid") else ["Frame validation failed"]
        )

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/api/stats")
async def get_statistics():
    """Get processing statistics"""
    return {
        "processed_total": len(results_store),
        "benchmarks_run": len(benchmark_store),
        "recent_results": list(results_store.keys())[-5:],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/export/csv")
async def export_csv():
    """Export results as CSV"""
    csv_content = "ID,Scenario,Reduction%,Time(ms)\n"
    for result in results_store.values():
        csv_content += f"{result.id},{result.scenario},{result.metrics.get('reduction_pct', 0)},{result.metrics.get('execution_time_ms', 0)}\n"

    return {
        "content": csv_content,
        "filename": f"comptext-results-{datetime.utcnow().isoformat()}.csv"
    }


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
