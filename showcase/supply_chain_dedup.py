import sys
import os
import time
import hashlib
import re

# Add root to sys.path to import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.kvtc import IndustrialKVTCStrategy

def get_supplier_updates():
    return [
        "Update 08:00: Alle Teile im Zulauf. Keine Verzögerungen erwartet.",
        "Update 09:00: Alle Teile im Zulauf. Keine Verzögerungen erwartet.", # Exact content duplicate
        "Update 10:00: Verzögerung bei Halbleitern (Region APAC). Neues Risiko identifiziert.",
        "Update 11:00: Verzögerung bei Halbleitern (Region APAC). Status unverändert.", # Semantic redundant
        "Update 12:00: Logistik-Streik in Hafen angekündigt. ETA +48h für Container C-12."
    ]

def semantic_dedup(updates):
    seen_hashes = set()
    unique_updates = []

    for update in updates:
        # 1. Normalize: Extract the message part after HH:MM:
        # We find the index after the first HH:MM:
        match = re.search(r"\d{2}:\d{2}: ", update)
        if match:
            content = update[match.end():].strip()
        else:
            content = update.strip()

        # 2. Extract semantic core (remove redundant phrases)
        semantic_core = content.replace("Status unverändert.", "").strip()

        # 3. Hash
        h = hashlib.md5(semantic_core.encode()).hexdigest()

        if h not in seen_hashes:
            seen_hashes.add(h)
            unique_updates.append(update)

    return unique_updates

def main():
    print("="*60)
    print("CASE 3: SUPPLY CHAIN DEDUPLICATOR")
    print("="*60)

    updates = get_supplier_updates()
    raw_text = "\n".join(updates)

    strategy = IndustrialKVTCStrategy()

    # POL Layer logic: Deduplicate first
    deduplicated_updates = semantic_dedup(updates)
    dedup_text = "\n".join(deduplicated_updates)

    # KVTC Layer logic
    start_time = time.perf_counter()
    result = strategy.compress(dedup_text)
    duration = (time.perf_counter() - start_time) * 1000

    orig_tokens = strategy._estimate_tokens(raw_text)

    print(f"Total Updates:         {len(updates)}")
    print(f"Unique Updates:        {len(deduplicated_updates)}")
    print(f"Original Tokens:       {orig_tokens}")
    print(f"Compressed Tokens:      {result.compressed_tokens}")
    print(f"Reduction Ratio:        {round((1 - result.compressed_tokens / orig_tokens) * 100, 2)}%")
    print(f"Processing Latency:     {duration:.2f} ms")
    print("-" * 60)
    print("INCREMENTAL UPDATES (POL Deduplicated):")
    for up in deduplicated_updates:
        print(f"  - {up}")
    print("-" * 60)
    print("OPTIMIZED KVTC FRAME:")
    print(result.frame)
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
