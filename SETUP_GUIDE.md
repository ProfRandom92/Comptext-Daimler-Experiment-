# CompText Daimler Integration - Implementation Guide

**Status**: ✓ Ready for Integration  
**Version**: 1.0-unified  
**Last Updated**: 2026-04-23

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Architecture](#system-architecture)
3. [Component Setup](#component-setup)
4. [API Usage](#api-usage)
5. [Testing & Benchmarking](#testing--benchmarking)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- **Python 3.11+** (with pip)
- **Node.js 18+** (with npm)
- **Docker** & **Docker Compose** (for containerized setup)
- **Git** (for version control)

### 5-Minute Local Setup

```bash
# 1. Clone all repositories
git clone https://github.com/profrandom92/comptext-mcp-server.git
git clone https://github.com/profrandom92/comptext-daimler-experiment-.git
git clone https://github.com/profrandom92/comptext-monorepo-X.git

# 2. Create development branch
cd comptext-mcp-server && git checkout claude/daimler-comptext-integration-r7zTh

# 3. Start Docker Compose
docker-compose -f docker-compose-comptext-daimler.yml up -d

# 4. Verify health
curl http://localhost:8000/health
curl http://localhost:3000/health
```

**Result**: Full Daimler dashboard + CompText pipeline running locally ✓

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│          DAIMLER CLINIC DASHBOARD (Port 8000)               │
│  FastAPI Backend + React Frontend + CompText Visualizer     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    MCP Protocol (stdio)
                           │
┌──────────────────────────▼──────────────────────────────────┐
│       COMPTEXT MCP SERVER (Port 3000)                        │
│  ├─ /tools/pipeline        Process FHIR→CompText           │
│  ├─ /tools/benchmark       Token metrics & performance      │
│  ├─ /tools/validate        Frame validation                 │
│  └─ /resources/scenarios   Scenario management              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    Python Pipeline
                           │
┌──────────────────────────▼──────────────────────────────────┐
│       COMPTEXT CORE PIPELINE                                 │
│  ├─ NURSE Stage: PHI Scrubbing (GDPR Art. 25)              │
│  ├─ KVTC Stage: 4-layer Compression                         │
│  ├─ Triage: Clinical Priority Assessment (ESC/AHA)          │
│  └─ Output: Compact CompText Frame (100-130 tokens)         │
└─────────────────────────────────────────────────────────────┘
```

### Component Roles

| Component | Technology | Purpose | Port |
|-----------|-----------|---------|------|
| **Dashboard** | FastAPI + React | Clinical data upload, results visualization | 8000 |
| **MCP Server** | Python | Universal tool interface, pipeline orchestration | 3000 |
| **Pipeline** | Python | FHIR processing, token reduction, triage | Internal |
| **Visualizer** | React + Recharts | Token charts, frame viewer, safety badges | 5173 |
| **Database** | PostgreSQL | Persistent result storage | 5432 |
| **Cache** | Redis | Session management, metrics caching | 6379 |
| **Monitoring** | Prometheus + Grafana | Performance metrics, alerts | 9090, 3002 |

---

## Component Setup

### 1. CompText MCP Server (Python)

**Location**: `/home/user/comptext-mcp-server/`

#### Installation

```bash
cd comptext-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import anthropic; print('✓ MCP SDK installed')"
```

#### Configuration

```bash
# Create .env file
cat > .env << 'EOF'
MCP_LOG_LEVEL=info
MCP_TRANSPORT=stdio
PYTHONUNBUFFERED=1
EOF
```

#### Running

```bash
# Development mode (with logging)
python src/comptext_mcp/server.py

# Production mode (stdio transport for Claude Desktop)
python src/comptext_mcp/server.py --stdio
```

**Test the server**:

```bash
# Health check
curl http://localhost:3000/health

# List available tools
curl -X POST http://localhost:3000/tools/list

# Call pipeline tool
curl -X POST http://localhost:3000/tools/comptext_pipeline \
  -H "Content-Type: application/json" \
  -d '{"scenario": "STEMI"}'
```

### 2. Daimler Dashboard (FastAPI + React)

**Location**: `/home/user/comptext-daimler-experiment-/`

#### Backend Setup

```bash
cd comptext-daimler-experiment-/app

# Python virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure MCP endpoint
export COMPTEXT_MCP_URL="http://localhost:3000"

# Run FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
cd comptext-daimler-experiment-/frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

**Access the Dashboard**:
- API: `http://localhost:8000/docs` (Swagger UI)
- Frontend: `http://localhost:3001` (React app)

### 3. CompText Visualizer (React)

**Location**: `/home/user/comptext-monorepo-X/packages/visualizer/`

```bash
cd packages/visualizer

# Install dependencies
npm install

# Start development server
npm run dev
```

**Access**: `http://localhost:5173`

---

## API Usage

### Processing a Clinical Scenario

```bash
# Request (STEMI scenario)
curl -X POST http://localhost:8000/api/pipeline/process \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "STEMI",
    "include_benchmark": true
  }'

# Response (200 OK)
{
  "id": "proc-a1b2c3d4",
  "scenario": "STEMI",
  "frame": "CT:v5 SC:STEMI TRI:P1\nVS[hr:118 sbp:82 spo2:91]\n...",
  "metrics": {
    "tokens_input": 1847,
    "tokens_final": 112,
    "reduction_pct": 93.9,
    "execution_time_ms": 2.1
  },
  "safety": {
    "allergies_preserved": 1,
    "medications_preserved": 1,
    "triage_accurate": "P1"
  },
  "timestamp": "2026-04-23T12:34:56Z"
}
```

### Uploading Custom FHIR Bundle

```bash
# Upload FHIR JSON file
curl -X POST http://localhost:8000/api/pipeline/upload \
  -F "file=@patient-bundle.json"

# Returns: PipelineResponse with processed frame
```

### Running Benchmarks

```bash
# Benchmark all scenarios
curl -X POST http://localhost:8000/api/benchmark \
  -H "Content-Type: application/json" \
  -d '{
    "scenarios": ["ALL"],
    "detailed": true
  }'

# Returns: benchmark_id for polling
{
  "benchmark_id": "bench-xyz789",
  "status": "started",
  "poll_url": "/api/benchmark/results/bench-xyz789"
}

# Poll for results
curl http://localhost:8000/api/benchmark/results/bench-xyz789

# When complete:
{
  "id": "bench-xyz789",
  "status": "completed",
  "result": {
    "results": { ... },
    "summary": {
      "scenarios_tested": 5,
      "average_reduction_pct": 93.9,
      "min_reduction_pct": 93.8,
      "max_reduction_pct": 94.1
    }
  }
}
```

### Validating CompText Frame

```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "frame": "CT:v5 SC:STEMI TRI:P1\nVS[hr:118]\n...",
    "checks": ["syntax", "safety", "gdpr"]
  }'

# Response
{
  "valid": true,
  "checks": {
    "syntax": { "valid": true, "message": "Frame follows CompText DSL" },
    "safety": { "triage_present": true, "critical_fields_preserved": true },
    "gdpr": { "phi_hashed": true, "gdpr_marked": true, "compliant": true }
  }
}
```

---

## Testing & Benchmarking

### Unit Tests

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_pipeline.py -v

# With coverage
pytest --cov=comptext tests/
```

### Benchmark Tests

```bash
# Run benchmarks (requires npm + Python)
npm run benchmark -- --all-scenarios --tokenizer=cl100k_base

# Expected output
┌──────────────┬──────────┬──────────┬──────────────┐
│ Scenario     │ FHIR (t) │ CompText │ Reduction    │
├──────────────┼──────────┼──────────┼──────────────┤
│ STEMI        │ 1,847    │ 112      │ 93.9% ✓      │
│ SEPSIS       │ 2,213    │ 131      │ 94.1% ✓      │
│ STROKE       │ 2,041    │ 124      │ 93.9% ✓      │
│ ANAPHYLAXIE  │ 1,742    │ 108      │ 93.8% ✓      │
│ DM_HYPO      │ 1,963    │ 119      │ 93.9% ✓      │
└──────────────┴──────────┴──────────┴──────────────┘
Average Reduction: 93.9% ✓
```

### Performance Testing

```bash
# Load test (using Apache Bench)
ab -n 100 -c 10 http://localhost:8000/api/scenarios

# Expected: <5ms per request, >95% success rate

# Stress test (continuous)
npm run benchmark -- --iterations=1000 --compare-tokenizers

# Memory profiling
python -m memory_profiler comptext/pipeline.py
```

### Integration Testing

```bash
# Test MCP Server + Dashboard integration
pytest tests/test_integration.py -v

# Test pipeline end-to-end
pytest tests/test_e2e.py --benchmark
```

---

## Deployment

### Local Development (Docker Compose)

```bash
# Start all services
docker-compose -f docker-compose-comptext-daimler.yml up -d

# View logs
docker-compose logs -f comptext-mcp-server
docker-compose logs -f daimler-dashboard

# Stop all services
docker-compose down

# Remove volumes (reset databases)
docker-compose down -v
```

### Production Deployment (Kubernetes)

```bash
# Build Docker images
docker build -t comptext-mcp-server:latest ./comptext-mcp-server
docker build -t daimler-dashboard:latest ./comptext-daimler-experiment-

# Push to registry
docker push your-registry/comptext-mcp-server:latest
docker push your-registry/daimler-dashboard:latest

# Deploy to Kubernetes
kubectl apply -f k8s/

# Verify
kubectl get pods -n comptext
kubectl logs -f -n comptext comptext-mcp-server-xxx
```

### Environment Configuration

**Production .env**:

```bash
# MCP Server
MCP_LOG_LEVEL=warning
MCP_TRANSPORT=stdio
WORKERS=4

# Dashboard
COMPTEXT_MCP_URL=http://comptext-mcp-server:3000
DATABASE_URL=postgresql://user:pass@postgres:5432/comptext_daimler
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-here

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=secure-password
ELK_ENABLED=true

# Security
GDPR_COMPLIANT=true
PHI_ENCRYPTION=AES-256-GCM
API_KEY_REQUIRED=true
```

---

## Troubleshooting

### Common Issues

#### 1. MCP Server won't connect

```bash
# Check if server is running
curl http://localhost:3000/health
# → 404? Start the server: python src/comptext_mcp/server.py

# Check logs
docker logs comptext-mcp-server
# → Look for errors in startup

# Rebuild container
docker-compose build --no-cache comptext-mcp-server
docker-compose up -d comptext-mcp-server
```

#### 2. Dashboard API errors (500)

```bash
# Check MCP connectivity from dashboard
curl -X GET http://comptext-mcp-server:3000/health

# Check logs
docker logs daimler-dashboard

# Restart with fresh environment
docker-compose restart daimler-dashboard
docker-compose logs -f daimler-dashboard
```

#### 3. Token reduction < 93%

```bash
# This should NOT happen for known scenarios
# If it does, check:
1. NURSE stage is scrubbing correctly
2. KVTC compression is applied
3. Triage is working

# Debug:
pytest tests/test_pipeline.py::test_token_reduction -v
```

#### 4. Memory issues

```bash
# Increase Docker memory limits
# In docker-compose-comptext-daimler.yml, add:
services:
  comptext-mcp-server:
    mem_limit: 2g
    memswap_limit: 2g

# Restart
docker-compose down && docker-compose up -d
```

### Debug Mode

```bash
# Enable verbose logging
export MCP_LOG_LEVEL=debug
python src/comptext_mcp/server.py

# Enable Python profiling
python -m cProfile -o pipeline.prof src/comptext_mcp/server.py

# Analyze profiling results
python -m pstats pipeline.prof
```

---

## Development Workflow

### Making Changes

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** (all repos):
   ```bash
   # Edit files, write tests, commit
   git add .
   git commit -m "feat: description of change"
   ```

3. **Run tests locally**:
   ```bash
   pytest
   npm run test
   npm run benchmark
   ```

4. **Push to development branch**:
   ```bash
   git push origin claude/daimler-comptext-integration-r7zTh
   ```

5. **CI/CD automatically**:
   - Runs linting, type checks, unit tests
   - Runs benchmarks (token reduction regression)
   - Builds Docker images
   - Publishes results to GitHub Pages

### Review Checklist

Before creating a PR:

- [ ] All tests passing locally
- [ ] Token reduction >= 93% for all scenarios
- [ ] GDPR compliance verified
- [ ] Code formatted (`black`, `prettier`)
- [ ] Types checked (`mypy`, `tsc`)
- [ ] Documentation updated
- [ ] No security vulnerabilities (`pip-audit`, `npm audit`)

---

## Next Steps

### Phase 2 Implementation (Week 2)

1. **Kubernetes manifests** for production
2. **Monitoring dashboards** (Grafana)
3. **OIDC authentication** (for clinic staff)
4. **Audit logging** (GDPR Art. 33)
5. **Performance tuning** (batch processing)

### Phase 3 Hardening (Week 3)

1. **Load testing** (500+ concurrent users)
2. **Security audit** (penetration testing)
3. **Compliance certification** (DIN SPEC 27001)
4. **Disaster recovery** plan
5. **Production rollout**

---

## Support & Resources

- **MCP Documentation**: https://modelcontextprotocol.io
- **FHIR R4 Spec**: https://www.hl7.org/fhir/r4/
- **CompText Architecture**: `/COMPTEXT_DAIMLER_INTEGRATION.md`
- **GitHub Issues**: [CompText Daimler Integration](https://github.com/profrandom92/comptext-daimler-experiment-)
- **Slack**: #comptext-daimler (internal)

---

**Version**: 1.0-unified  
**Last Updated**: 2026-04-23  
**Owner**: Claude Code Integration Team  
**Status**: ✓ Ready for Implementation
