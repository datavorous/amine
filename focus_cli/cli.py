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

# Ensure the data directory exists
def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

# Show guidelines and recent stats
def show_guidelines(recent_stats: List[Dict]):
    guideline_text = """
    [bold red]🔥 Start:[/bold red] Set your sessions, focus time, and break times.
    [bold red]🛑 Exit:[/bold red] Press [bold white]{exit_combo}[/bold white] to quit anytime.
    [bold red]📊 Stats:[/bold red] Review your recent sessions below.
    """.format(exit_combo=CONFIG['EXIT_COMBO'])

    console.print(Panel(guideline_text, title="[bold red]🚀 Pomodoro Guidelines[/bold red]", border_style="red"))

    if recent_stats:
        table = Table(title="📅 Recent Sessions", title_style="bold red", style="bright_red")
        table.add_column("📆 Date", style="bold white")
        table.add_column("⏱️ Count", style="bold white")
        table.add_column("⌛ Duration", style="bold white")

        for session in recent_stats:
            table.add_row(session["date"], str(session["pomodoros"]), f"{session['focus_duration']}m")

        console.print(Align.center(table))
    else:
        console.print("[red]No recent data available.[/red]")

# Load recent stats from the JSON file
def load_recent_stats() -> List[Dict]:
    try:
        return json.loads(DATA_FILE.read_text())[-5:] if DATA_FILE.exists() else []
    except Exception as e:
        console.print(f"[red]Error loading stats: {e}[/red]")
        return []

# Save focus session data to the JSON file
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
        console.print(f"[red]Error saving data: {e}[/red]")

# Main pomodoro flow
def pomodoro_flow():
    ensure_data_dir()
    show_guidelines(load_recent_stats())

    pomodoros = int(Prompt.ask("[red]💼 Number of Sessions[/red]", default="4"))
    focus_duration = int(Prompt.ask("[red]⏳ Focus Duration (min)[/red]", default="25"))
    break_duration = int(Prompt.ask("[red]☕ Break Duration (min)[/red]", default="5"))
    website = Prompt.ask("[red]🌐 Focus URL[/red]", default="https://example.com")

    console.print(Panel(
        f"[red]{pomodoros} x {focus_duration}m focus / {break_duration}m break[/red]\n"
        f"[red]🌐 URL:[/red] {website}\n"
        f"[red]🛑 Stop:[/red] {CONFIG['EXIT_COMBO']}",
        title="[bold red]🎯 Pomodoro Config[/bold red]",
        border_style="red"
    ))

    if Prompt.ask("[red]🚀 Ready to start?[/red]", choices=["y", "n"], default="y") != "y":
        console.print("[red]Cancelled.[/red]")
        return

    webbrowser.open(website)

    for i in range(pomodoros):
        console.print(f"[red]🍅 Pomodoro {i + 1}/{pomodoros} starting...[/red]")
        countdown_timer(10)

        FocusProtection().start_protection(focus_duration)

        if i < pomodoros - 1:
            console.print(f"[red]☕ Break: {break_duration}m[/red]")
            countdown_timer(break_duration * 60)

    console.print("[red]🎉 Pomodoro session completed![/red]")
    save_focus_session(pomodoros, focus_duration)

@click.command()
def pomodoro():
    pomodoro_flow()

if __name__ == '__main__':
    pomodoro()
