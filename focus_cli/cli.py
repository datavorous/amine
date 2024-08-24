import sys
import os
import webbrowser
import json
from pathlib import Path
from typing import List, Dict
import click
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from datetime import datetime
from .focus_protection import FocusProtection
from .config import CONFIG
from .utils import countdown_timer

console = Console()

DATA_DIR = Path.home() / ".pomodoro_cli"
DATA_FILE = DATA_DIR / "pomodoro_stats.json"

def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def show_guidelines(recent_stats: List[Dict]):
    guideline_text = """
    [bold white]Start[/bold white]: Set sessions, focus, break times.
    [bold white]Exit[/bold white]: Press [bold white]{exit_combo}[/bold white].
    [bold white]Stats[/bold white]: Recent data below.
    """.format(exit_combo=CONFIG['EXIT_COMBO'])

    console.print(Panel(guideline_text, title="[bold white]Pomodoro Guidelines[/bold white]", border_style="white"))

    if recent_stats:
        table = Table(title="Recent Sessions", style="white")
        table.add_column("Date", style="white")
        table.add_column("Count", style="white")
        table.add_column("Duration", style="white")

        for session in recent_stats:
            table.add_row(session["date"], str(session["pomodoros"]), f"{session['focus_duration']}m")

        console.print(Align.center(table))
    else:
        console.print("[white]No recent data.[/white]")

def load_recent_stats() -> List[Dict]:
    try:
        return json.loads(DATA_FILE.read_text())[-5:] if DATA_FILE.exists() else []
    except Exception as e:
        console.print(f"[white]Error loading stats: {e}[/white]")
        return []

def save_focus_session(pomodoros: int, focus_duration: int):
    try:
        data = load_recent_stats()
        data.append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "pomodoros": pomodoros,
            "focus_duration": focus_duration
        })
        DATA_FILE.write_text(json.dumps(data))
    except Exception as e:
        console.print(f"[white]Error saving data: {e}[/white]")

def pomodoro_flow():
    ensure_data_dir()
    show_guidelines(load_recent_stats())

    pomodoros = int(Prompt.ask("[white]Sessions[/white]", default="4"))
    focus_duration = int(Prompt.ask("[white]Focus (min)[/white]", default="25"))
    break_duration = int(Prompt.ask("[white]Break (min)[/white]", default="5"))
    website = Prompt.ask("[white]Focus URL[/white]", default="https://example.com")

    console.print(Panel(
        f"[white]{pomodoros} x {focus_duration}m focus / {break_duration}m break[/white]\n"
        f"[white]URL:[/white] {website}\n"
        f"[white]Stop:[/white] {CONFIG['EXIT_COMBO']}",
        title="[bold white]Pomodoro Config[/bold white]",
        border_style="white"
    ))

    if Prompt.ask("[white]Start?[/white]", choices=["y", "n"], default="y") != "y":
        console.print("[white]Cancelled.[/white]")
        return

    webbrowser.open(website)

    for i in range(pomodoros):
        console.print(f"[white]Pomodoro {i + 1}/{pomodoros} starting...[/white]")
        countdown_timer(10)

        FocusProtection().start_protection(focus_duration)

        if i < pomodoros - 1:
            console.print(f"[white]Break: {break_duration}m[/white]")
            countdown_timer(break_duration * 60)

    console.print("[white]Pomodoro completed![/white]")
    save_focus_session(pomodoros, focus_duration)

@click.command()
def pomodoro():
    pomodoro_flow()

if __name__ == '__main__':
    pomodoro()
