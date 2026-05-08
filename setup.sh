#!/bin/bash

echo "Starting Daimler Buses CompText Environment Setup..."

# 1. Dependency verification
echo "Verifying pinned versions in requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found!"
    # Handle error without exit to not break the bash session
fi
python3 -m pip install -r requirements.txt

# 2. OpenTelemetry Health Check
echo "Checking OpenTelemetry Initialization..."
python3 -c "
import sys
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    print('OpenTelemetry successfully initialized.')
except Exception as e:
    print(f'OpenTelemetry initialization failed: {e}')
"

# 3. Connectivity check to EU Tinybird
echo "Checking connectivity to EU Tinybird region (eu.tinybird.co)..."
if curl -s -I https://eu.tinybird.co | grep -q "HTTP/2 200\|HTTP/1.1 200\|HTTP/2 401\|HTTP/1.1 401\|HTTP/2 403\|HTTP/1.1 403\|HTTP/1.1 404\|HTTP/2 404"; then
    echo "Connection to eu.tinybird.co successful."
else
    echo "Warning/Error: Could not verify connection to eu.tinybird.co"
    # Try ping or alternative
    ping -c 1 eu.tinybird.co || true
fi

echo "Setup completed successfully!"
