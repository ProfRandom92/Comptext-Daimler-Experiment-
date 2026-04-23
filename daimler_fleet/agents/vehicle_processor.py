import re
from rich.panel import Panel
from rich.text import Text

class VehicleDataProcessor:
    def __init__(self):
        self.obd_keywords = {
            "rpm", "speed", "temp", "pressure", "fuel", "o2", "throttle",
            "battery", "voltage", "amperage", "load", "coolant", "oil",
            "transmission", "gear", "brake", "abs", "esp", "traction",
            "mileage", "distance", "km", "mph", "acceleration", "torque",
            "lambda", "nox", "pm", "emissions", "exhaust"
        }

        self.fault_codes = {
            "p0", "p1", "p2", "p3", "c0", "c1", "b0", "b1", "u0", "u1",
            "dtc", "error", "fault", "warning", "critical", "malfunction"
        }

        self.vehicle_models = {
            "a-klasse", "c-klasse", "e-klasse", "s-klasse", "glc", "gle", "gls",
            "amg", "maybach", "eqe", "eqs", "sprinter", "vito", "actros"
        }

    def process(self, raw_diagnostic, console):
        clean_text = re.sub(r'([.,;:])', r' \1 ', raw_diagnostic)
        words = clean_text.split()

        signals = []
        processed_text = Text()

        for w in words:
            w_check = w.lower().strip(".,;:")
            is_signal = False

            # Check for OBD keywords, fault codes, or vehicle models
            if (any(c.isdigit() for c in w) or
                w_check in self.obd_keywords or
                any(fc in w_check for fc in self.fault_codes) or
                any(vm in w_check for vm in self.vehicle_models) or
                (w.isupper() and len(w) < 5)):
                is_signal = True

            if w in ".,;:":
                processed_text.append(f"{w} ", style="white")
                continue

            if is_signal:
                signals.append(w)
                processed_text.append(f"{w} ", style="bold cyan")
            else:
                processed_text.append(f"{w} ", style="dim yellow strike")

        console.print(Panel(processed_text, title="[bold magenta]Vehicle Data Processor: OBD-II Filter[/]", border_style="magenta"))

        comp_text = " ".join(signals)

        # Simple token counting
        raw_tok = len(raw_diagnostic.split())
        comp_tok = len(comp_text.split())

        ratio = (1 - (comp_tok / raw_tok)) * 100 if raw_tok > 0 else 0
        saved_bytes = len(raw_diagnostic.encode('utf-8')) - len(comp_text.encode('utf-8'))

        return {
            "comp_text": comp_text,
            "raw_tok": raw_tok,
            "comp_tok": comp_tok,
            "ratio": f"{ratio:.1f}%",
            "saved_bytes": saved_bytes
        }
