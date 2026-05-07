import time

import requests

BASE_URL = "https://comptext-daimler-final-jules.onrender.com"

SCENARIOS = [
    {
        "name": "Szenario 1: Token-Reduktion (Wartung)",
        "payload": {
            "text": "Wartungsauftrag Actros 2026\nSOP-1: Bremsenprüfung\nSOP-2: Ölwechsel\nHistorie 2024: OK\nHistorie 2023: OK\nHistorie 2022: OK\nBefund: Beläge verschlissen.",
            "quelle": "SAP-MOCK"
        }
    },
    {
        "name": "Szenario 2: Datenschutz & DSGVO (Produktion)",
        "payload": {
            "text": "Produktionsbericht Mitarbeiter P9912345\nFahrzeug FIN: WDB9630011L123456\nKontakt: info@logistik-beispiel.de\nStatus: Montage abgeschlossen.",
            "quelle": "MES-PROD"
        }
    }
]

def run_showcase():
    print("=" * 60)
    print("🚀 DAIMLER COMPTEXT KERNEL SHOWCASE")
    print("=" * 60)

    for s in SCENARIOS:
        print(f"\n▶ Running: {s['name']}")
        t0 = time.perf_counter()
        try:
            resp = requests.post(f"{BASE_URL}/analyze", json=s['payload'], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            latency = (time.perf_counter() - t0) * 1000

            print("  - Status: ✅ Success")
            print(f"  - Latency: {latency:.2f}ms")
            print(f"  - Tokens: {data['token_original']} (Raw) -> {data['token_komprimiert']} (Comp)")
            print(f"  - Savings: {data['token_einsparung_pct']}%")
            print(f"  - Summary: {data['compression_summary']}")
            print(f"  - Sanitization: {', '.join(data['bereinigungen']) if data['bereinigungen'] else 'None'}")
            print(f"  - Audit Fingerprint: {data['audit_trail']['checksum']}")
        except Exception as e:
            print(f"  - Status: ❌ Failed: {e}")

    print("\n" + "=" * 60)
    print("📈 FINAL STATS FROM LIVE SERVER")
    try:
        stats = requests.get(f"{BASE_URL}/stats").json()
        print(f"  - Server Uptime: {stats['uptime_seconds']}s")
        print(f"  - Total Tokens Saved: {stats['total_token_savings_pct']}%")
        print(f"  - Processed Bytes: {stats['processed_compressed_bytes']}")
    except Exception:
        print("  - Stats unavailable.")
    print("=" * 60)

if __name__ == "__main__":
    run_showcase()
