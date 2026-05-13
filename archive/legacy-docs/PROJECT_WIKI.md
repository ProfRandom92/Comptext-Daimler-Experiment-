# CompText-Daimler-Experiment (V6) Knowledge Base

## Architecture
The V6 Kernel features a highly optimized 4-Layer Key-Value-Type-Code (KVTC) Compression structure designed specifically for industrial logs.
- **Compression Efficiency**: Achieves up to 94% reduction in token count while preserving structured elements like OBD codes and SAP numbers.
- **Layers**:
  - **K (Key)**: Extracts field labels.
  - **V (Value)**: Extracts field values.
  - **T (Type)**: Identifies data type categories (Numbers, Codes, Text, Dates).
  - **C (Code)**: Retains structured codes like OBD, SAP numbers, and FIN fragments.
- **Sandwich Zones**:
  - **Header (Lossless)**: Preserves critical SOPs, vehicle master data, and system context.
  - **Middle (Aggressive)**: Compresses historical maintenance entries and old production data by retaining only high-density information.
  - **Window (Lossless)**: Preserves current diagnostic data and open orders.

## Design DNA
The UI/UX is built to seamlessly blend with the Mercedes-Benz corporate identity:
- **Grid System**: Strict adherence to an 8px grid system for layout consistency.
- **Typography**: Complete integration of the **MB Corpo** font family for all text elements.
- **Color Palette**:
  - Primary Brand Blue: `#0067B1`
  - Warning/Accent Orange: `#E66000`

## Security
The platform incorporates enterprise-grade security measures suitable for Daimler's operational requirements:
- **Sanitization**: Advanced `nh3` HTML sanitization logic is used to neutralize potential XSS and injection attacks on inputs and rendered markdown.
- **Data Privacy**: Complete **DSGVO-compliant telemetry routing**, ensuring all PII (such as FIN numbers) is masked or stripped before transmission to analytics backends or LLM providers. OpenTelemetry configuration securely manages distributed tracing without leaking sensitive context.

## Infrastructure
The backend is deployed via Render, and the frontend is built with React.
- **Live Demo:** https://comptext-daimler-api.onrender.com
- **Region:** Frankfurt
- **Persistent Cache:** 10GB disk mounted at `/cache`
- **Security Hardening:** Strict CORS enforced via `ALLOWED_ORIGINS`. Checksum hashing utilizes collision-resistant SHA-256 (replaced MD5).
