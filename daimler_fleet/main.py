import sys
import time
import os

sys.path.append(os.getcwd())

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.align import Align
from rich import print as rprint

from daimler_fleet.database.storage import FleetStorage
from daimler_fleet.agents.vehicle_processor import VehicleDataProcessor
from daimler_fleet.agents.diagnostic_evaluator import DiagnosticEvaluator

def main():
    console = Console()
    db = FleetStorage()
    processor = VehicleDataProcessor()
    evaluator = DiagnosticEvaluator()

    while True:
        console.clear()
        header = """[bold white]DAIMLER FLEET[/] [bold yellow]×[/] [bold cyan]DIAGNOSTIC SYSTEM v1[/]
[dim]Vehicle Data Compression & Predictive Maintenance[/]
[bold black on cyan] 🚗 SYSTEM ONLINE [/]"""
        console.print(Panel(Align.center(header), border_style="cyan"))

        choice = Prompt.ask(
            "\n[1] New Diagnostic\n[2] Fleet History\n[3] Export JSON\n[4] Exit",
            choices=["1", "2", "3", "4"]
        )

        if choice == "4":
            break

        if choice == "3":
            with console.status("[bold blue]Exporting fleet data...[/]"):
                time.sleep(1)
                count = db.export_json()
            rprint(f"[green]✓ Exported {count} diagnostic cases.[/]")
            Prompt.ask("Continue")

        if choice == "2":
            rows = db.get_fleet_history()
            if not rows:
                rprint("[yellow]No fleet history yet.[/]")
                Prompt.ask("Continue")
                continue

            t = Table(title="Fleet Diagnostic History")
            t.add_column("Vehicle ID", style="cyan")
            t.add_column("Timestamp", style="white")
            t.add_column("Severity", style="magenta")
            t.add_column("Fault Code", style="yellow")
            t.add_column("Compression", style="green")

            for r in rows:
                severity_style = "bold red" if "CRITICAL" in r[2] else "bold yellow" if "WARNING" in r[2] else "green"
                t.add_row(r[0], r[1], f"[{severity_style}]{r[2]}[/]", r[3], r[4])

            console.print(t)
            Prompt.ask("Continue")

        if choice == "1":
            raw = console.input("\n[bold cyan]🔧 Vehicle Data Processor listening...[/]\n[bold]Input diagnostic data:[/]\n> ")
            if not raw.strip():
                continue

            rprint("\n[dim]--- Phase 1: Data Compression ---[/]")
            time.sleep(0.3)
            proc_res = processor.process(raw, console)

            rprint("\n[dim]--- Phase 2: Diagnostic Evaluation ---[/]")
            time.sleep(0.3)
            eval_res = evaluator.evaluate(proc_res["comp_text"])

            case_data = {
                "vehicle_id": eval_res["vehicle_id"],
                "severity": eval_res["severity"],
                "fault_code": eval_res["fault_code"],
                "ratio": proc_res["ratio"],
                "maintenance_due": eval_res["maintenance_due"]
            }
            db.save_diagnostic(case_data)

            severity_col = "red" if "CRITICAL" in eval_res["severity"] else "yellow" if "WARNING" in eval_res["severity"] else "green"
            rprint(f"\n[bold {severity_col}]>>> {eval_res['severity']} - {eval_res['fault_code']}[/]")
            rprint(f"[dim]Saved {proc_res['saved_bytes']} bytes bandwidth.[/]")

            if eval_res["maintenance_due"]:
                rprint("[bold yellow]⚠️  Maintenance service recommended![/]")

            Prompt.ask("Next diagnostic")

if __name__ == "__main__":
    main()
