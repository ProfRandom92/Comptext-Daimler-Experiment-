import sys
import os
import time
import random
import hashlib

# Add root to sys.path to import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.kvtc import IndustrialKVTCStrategy

def generate_xentry_log(lines=5000):
    log = []
    for i in range(lines):
        ts = f"{12:02}:{i//3600:02}:{(i//60)%60:02}.{i%100:02}"
        r = random.random()
        if r < 0.005:
            log.append(f"{ts} [ECU_01] ERROR: Fault State detected - Code: B1202")
        elif r < 0.01:
            log.append(f"{ts} [ECU_02] ALERT: Error-ID 0xFA32 - Communication Loss")
        elif r < 0.015:
            voltage = round(random.uniform(9.0, 11.2), 1)
            log.append(f"{ts} [POWER] WARN: Critical Voltage Drop - {voltage}V")
        else:
            v = round(random.uniform(12.5, 14.2), 1)
            log.append(f"{ts} [INFO] System Heartbeat - Voltage: {v}V - Status: OK")
    return "\n".join(log)

def filter_log(log_text):
    relevant_keywords = ["Fault State", "Error-ID", "Critical Voltage Drop"]
    lines = log_text.splitlines()
    filtered = [line for line in lines if any(k in line for k in relevant_keywords)]
    return "\n".join(filtered)

def main():
    print("="*60)
    print("CASE 1: XENTRY DIAGNOSE-LOG OPTIMIZER")
    print("="*60)

    raw_log = generate_xentry_log(5500)
    strategy = IndustrialKVTCStrategy()

    start_time = time.perf_counter()
    filtered_log = filter_log(raw_log)
    result = strategy.compress(filtered_log)
    duration = (time.perf_counter() - start_time) * 1000

    orig_tokens = strategy._estimate_tokens(raw_log)

    print(f"Original Log Size:   {len(raw_log.splitlines())} lines")
    print(f"Filtered Log Size:   {len(filtered_log.splitlines())} lines")
    print(f"Original Tokens (est): {orig_tokens}")
    print(f"Compressed Tokens:    {result.compressed_tokens}")
    print(f"Reduction Ratio:      {round((1 - result.compressed_tokens / orig_tokens) * 100, 2)}%")
    print(f"Processing Latency:   {duration:.2f} ms")
    print(f"KVTC Checksum:        {result.checksum}")
    print("-" * 60)
    print("OPTIMIZED KVTC FRAME (Sample):")
    print(result.frame[:200] + "...")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
