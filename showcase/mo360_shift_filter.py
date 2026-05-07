import sys
import os
import time
import re

# Add root to sys.path to import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.kvtc import IndustrialKVTCStrategy

def get_sample_shift_report():
    return """
Schichtbericht - Factory 56 - 07.05.2024
Schicht: Frühschicht
Linie: Montage 2

06:00: Schichtbeginn. Alle Systeme im Normalbetrieb.
06:15: Station 12: Normalbetrieb.
06:30: Station 14: Normalbetrieb.
07:00: Stopp an Station 22: Materialmangel bei Türverkleidungen. Dauer: 15min.
07:15: Station 22 wieder im Normalbetrieb nach Materialnachlieferung.
07:30: Normalbetrieb an allen Stationen.
08:00: Station 5: Werkzeugbruch an Schrauber S3. Wartung informiert.
08:20: Station 5: Schrauber S3 getauscht. Produktion läuft weiter.
09:00: Kaffeepause.
09:30: Wiederaufnahme. Normalbetrieb.
10:00: Station 45: Sensorfehler an Förderband. Kleiner Stopp (2min).
11:00: Normalbetrieb.
12:00: Schichtende. Zusammenfassung: 2 größere Stopps, 1 Kleinstopp.
"""

def extract_deviations(report_text):
    lines = report_text.splitlines()
    deviations = []

    # Process header
    for line in lines[:5]:
        if "Schicht:" in line or "Linie:" in line or "Factory" in line:
            deviations.append(line.strip())

    # Extract deviations with structured KV approach
    for line in lines:
        if "Normalbetrieb" in line or "Schichtbeginn" in line or "Pause" in line or "Wiederaufnahme" in line:
            continue

        # Match timestamped lines: HH:MM: Text
        match = re.match(r"^(\d{2}:\d{2}):\s*(.*)", line)
        if match:
            ts, msg = match.groups()
            # Convert to a KV structure
            deviations.append(f"Timestamp={ts} | Event={msg}")
        elif "Zusammenfassung" in line:
            deviations.append(f"Summary={line.split(':', 1)[1].strip() if ':' in line else line.strip()}")

    return "\n".join(deviations)

def main():
    print("="*60)
    print("CASE 2: MO360 SCHICHTBERICHT-FILTER")
    print("="*60)

    raw_report = get_sample_shift_report()
    strategy = IndustrialKVTCStrategy()

    start_time = time.perf_counter()
    structured_deviations = extract_deviations(raw_report)
    result = strategy.compress(structured_deviations)
    duration = (time.perf_counter() - start_time) * 1000

    orig_tokens = strategy._estimate_tokens(raw_report)

    print(f"Original Report Tokens: {orig_tokens}")
    print(f"Compressed Tokens:      {result.compressed_tokens}")
    print(f"Reduction Ratio:        {round((1 - result.compressed_tokens / orig_tokens) * 100, 2)}%")
    print(f"Processing Latency:     {duration:.2f} ms")
    print(f"KVTC Checksum:          {result.checksum}")
    print("-" * 60)
    print("FILTERED & STRUCTURED REPORT (POL Layer):")
    print(structured_deviations)
    print("-" * 60)
    print("OPTIMIZED KVTC FRAME (Final):")
    print(result.frame)
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
