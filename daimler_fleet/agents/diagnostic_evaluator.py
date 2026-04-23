import time

class DiagnosticEvaluator:
    def __init__(self):
        self.critical_faults = [
            "p0016", "p0100", "p0128", "p0201", "p0300", "p0400", "p0500",
            "p0600", "p0700", "c0035", "c0040", "c0050", "c0096", "u0001"
        ]

        self.warning_faults = [
            "p0101", "p0102", "p0103", "p0106", "p0107", "p0108",
            "c0012", "c0013", "c0014", "b0012", "b0013"
        ]

        self.maintenance_triggers = ["mileage", "hours", "service", "oil", "filter", "brake"]

    def evaluate(self, comp_text):
        vehicle_id = f"DA-{int(time.time()) % 1000000:06d}"
        text_lower = comp_text.lower()

        is_critical = any(fault in text_lower for fault in self.critical_faults)
        is_warning = any(fault in text_lower for fault in self.warning_faults)
        needs_maintenance = any(trigger in text_lower for trigger in self.maintenance_triggers)

        if is_critical:
            severity = "🔴 CRITICAL"
            fault_code = "P0-CRITICAL"
        elif is_warning:
            severity = "🟡 WARNING"
            fault_code = "P0-WARNING"
        else:
            severity = "🟢 OK"
            fault_code = "P0-OK"

        return {
            "vehicle_id": vehicle_id,
            "severity": severity,
            "fault_code": fault_code,
            "maintenance_due": needs_maintenance
        }
