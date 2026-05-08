import os
import sys

# Add root to sys.path to import src and showcase
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from showcase.mo360_shift_filter import extract_deviations
from showcase.supply_chain_dedup import semantic_dedup
from showcase.xentry_optimizer import filter_log
from src.core.kvtc import IndustrialKVTCStrategy


def test_xentry_optimizer_determinism():
    sample_log = (
        "12:00:00.01 [ECU_01] ERROR: Fault State detected - Code: B1202\n"
        "12:00:00.02 [INFO] Heartbeat\n"
        "12:00:00.03 [POWER] WARN: Critical Voltage Drop - 10.5V"
    )

    filtered1 = filter_log(sample_log)
    filtered2 = filter_log(sample_log)

    assert filtered1 == filtered2
    assert "Fault State" in filtered1
    assert "Critical Voltage Drop" in filtered1
    assert "Heartbeat" not in filtered1

    strategy = IndustrialKVTCStrategy()
    res1 = strategy.compress(filtered1)
    res2 = strategy.compress(filtered1)

    assert res1.checksum == res2.checksum


def test_mo360_shift_filter_determinism():
    sample_report = (
        "Schichtbericht - Factory 56\n"
        "Schicht: Frühschicht\n"
        "06:00: Schichtbeginn. Normalbetrieb.\n"
        "07:00: Stopp an Station 22: Materialmangel."
    )

    extracted1 = extract_deviations(sample_report)
    extracted2 = extract_deviations(sample_report)

    assert extracted1 == extracted2
    assert "Materialmangel" in extracted1
    assert "Normalbetrieb" not in extracted1

    strategy = IndustrialKVTCStrategy()
    res1 = strategy.compress(extracted1)
    res2 = strategy.compress(extracted1)

    assert res1.checksum == res2.checksum


def test_supply_chain_dedup_determinism():
    updates = [
        "Update 08:00: Alle Teile im Zulauf.",
        "Update 09:00: Alle Teile im Zulauf.",
        "Update 10:00: Verzögerung bei Halbleitern.",
    ]

    dedup1 = semantic_dedup(updates)
    dedup2 = semantic_dedup(updates)

    assert dedup1 == dedup2
    assert len(dedup1) == 2

    strategy = IndustrialKVTCStrategy()
    res1 = strategy.compress("\n".join(dedup1))
    res2 = strategy.compress("\n".join(dedup1))

    assert res1.checksum == res2.checksum
