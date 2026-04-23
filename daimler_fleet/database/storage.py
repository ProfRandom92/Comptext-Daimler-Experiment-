import sqlite3
import json
from datetime import datetime

DB_FILE = "daimler_fleet.db"

class FleetStorage:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS fleet_cases (
            vehicle_id TEXT,
            timestamp TEXT,
            severity TEXT,
            fault_code TEXT,
            compression_ratio TEXT,
            maintenance_due BOOLEAN
        )""")
        self.conn.commit()

    def save_diagnostic(self, case_data):
        self.conn.execute(
            "INSERT INTO fleet_cases VALUES (?,?,?,?,?,?)",
            (case_data["vehicle_id"], datetime.now().isoformat(),
             case_data["severity"], case_data["fault_code"],
             case_data["ratio"], case_data.get("maintenance_due", False))
        )
        self.conn.commit()

    def get_fleet_history(self, limit=10):
        cursor = self.conn.execute(
            "SELECT vehicle_id, timestamp, severity, fault_code, compression_ratio FROM fleet_cases ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return cursor.fetchall()

    def export_json(self, filename="daimler_export.json"):
        cursor = self.conn.execute("SELECT * FROM fleet_cases")
        rows = cursor.fetchall()
        data = [
            {
                "vehicle_id": r[0],
                "timestamp": r[1],
                "severity": r[2],
                "fault_code": r[3],
                "compression_ratio": r[4],
                "maintenance_due": bool(r[5])
            }
            for r in rows
        ]
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        return len(data)
