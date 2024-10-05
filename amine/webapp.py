import sys
import time
import sqlite3
import logging
import keyboard
import winsound
import pyautogui
import threading
import subprocess
import webbrowser
import matplotlib
import pandas as pd
import seaborn as sns
from io import BytesIO
import pygetwindow as gw
from flask import send_file
import plotly.express as px
from plyer import notification
import matplotlib.pyplot as plt
from flaskwebgui import FlaskUI
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
matplotlib.use("Agg")

CONFIG = {
    "SAFE_X": 500,
    "SAFE_Y": 500,
    "TOP_SCREEN_THRESHOLD": 50,
    "BLOCKED_KEYS": [
        "left windows",
        "right windows",
        "alt",
        "tab",
        "ctrl",
        "esc",
        "f11",
        "cmd",
        "command",
        "win",
    ],
    "EXIT_COMBO": "ctrl+shift+q",
    "MOUSE_ENFORCE_DELAY": 0.08,
}


def setup_logging():
    logger = logging.getLogger("amine")
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("amine.log")
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


class FocusProtection:
    def __init__(self, config=CONFIG, session_id=None):
        self.config = config
        self.mouse_thread = None
        pyautogui.FAILSAFE = False
        self.session_id = session_id
        self.protection_active = False
        self.key_tracking_thread = None
        self.fullscreen_tracking_thread = None

    def track_key_attempts(self):
        logger.info("Tracking Key Press Attempts.")

        def on_key_event(event):
            if event.name in self.config["BLOCKED_KEYS"]:
                logger.warning(f"Attempted To Press Blocked Key : {event.name}")
                log_distraction(self.session_id, f"Blocked Key Press : {event.name}")
                winsound.Beep(500, 500)

        keyboard.hook(on_key_event)

        while self.protection_active:
            time.sleep(1)

        keyboard.unhook(on_key_event)

    def track_fullscreen_exit(self):
        logger.info("Tracking Fullscreen Exists.")
        screen_width, screen_height = pyautogui.size()
        tolerance = 10

        while self.protection_active:
            try:
                windows = gw.getWindowsWithTitle("amine")
                if windows:
                    window = windows[0]
                    if (
                        window.width <= screen_width - tolerance
                        or window.height <= screen_height - tolerance
                    ):
                        pass
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error Tracking Fullscreen: {e}")

    def enforce_mouse_boundaries(self):
        edge_threshold = 50
        screen_width, screen_height = pyautogui.size()
        logger.info("Mouse Boundary Enforcement Started.")
        while self.protection_active:
            try:
                x, y = pyautogui.position()
                if (
                    x <= edge_threshold
                    or y <= edge_threshold
                    or y >= screen_height - edge_threshold
                    or y <= self.config["TOP_SCREEN_THRESHOLD"]
                ):
                    pyautogui.moveTo(self.config["SAFE_X"], self.config["SAFE_Y"])
                    log_distraction(self.session_id, "Mouse Boundary Violation")
                time.sleep(self.config["MOUSE_ENFORCE_DELAY"])
            except Exception as e:
                logger.error(f"Error Enforcing Mouse Boundaries: {e}")
        logger.info("Mouse Boundary Enforcement Ended.")

    def block_keys(self):
        logger.info("Blocking Keys.")
        try:
            for key in self.config["BLOCKED_KEYS"]:
                keyboard.block_key(key)
        except Exception as e:
            logger.error(f"Error Blocking Keys: {e}")

    def unblock_keys(self):
        logger.info("Unblocking All Keys.")
        try:
            keyboard.unhook_all()
        except Exception as e:
            logger.error(f"Error Unblocking Keys: {e}")

    def block_distractions(self, duration_minutes):
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        self.block_keys()
        self.protection_active = True

        self.mouse_thread = threading.Thread(
            target=self.enforce_mouse_boundaries, daemon=True
        )
        self.key_tracking_thread = threading.Thread(
            target=self.track_key_attempts, daemon=True
        )
        self.fullscreen_tracking_thread = threading.Thread(
            target=self.track_fullscreen_exit, daemon=True
        )

        self.mouse_thread.start()
        self.key_tracking_thread.start()
        self.fullscreen_tracking_thread.start()

        try:
            while datetime.now() < end_time:
                if keyboard.is_pressed(self.config["EXIT_COMBO"]):
                    logger.info("Exit Combo Pressed, Exiting.")
                    break
                time.sleep(0.1)
        finally:
            self.protection_active = False
            self.mouse_thread.join()
            self.key_tracking_thread.join()
            self.fullscreen_tracking_thread.join()
            self.unblock_keys()
            logger.info(
                f"Distraction Blocking Finished After {duration_minutes} Minutes."
            )

    def start_protection(self, duration_minutes):
        logger.info(f"Starting Focus Protection For {duration_minutes} Minutes.")
        self.block_distractions(duration_minutes)


def notify_user(message):
    logger.info(f"Sending notification: {message}")
    try:
        notification.notify(title="Amine Pomodoro", message=message, timeout=10)
    except Exception as e:
        logger.error(f"Error Sending Notification: {e}")


def init_db():
    try:
        with sqlite3.connect("amine_data.db") as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT,
                    end_time TEXT,
                    total_duration INTEGER
                )
            """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS distractions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    event_type TEXT,
                    event_time TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
            """
            )
        logger.info("Database Initialized Successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database Initialization Error: {e}")


def log_distraction(session_id, event_type):
    try:
        with sqlite3.connect("amine_data.db") as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO distractions (session_id, event_type, event_time) VALUES (?, ?, ?)",
                (session_id, event_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
        logger.info(f"Distraction logged: {event_type}")
    except sqlite3.Error as e:
        logger.error(f"Error logging distraction: {e}")


def save_session_data(start_time, end_time, total_duration):
    try:
        with sqlite3.connect("amine_data.db") as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions (start_time, end_time, total_duration) VALUES (?, ?, ?)",
                (start_time, end_time, total_duration),
            )
        logger.info("Session data saved successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error saving session data: {e}")


def manage_flask_window(action):
    logger.info(f"{action.capitalize()}ing Flask window.")
    try:
        windows = gw.getWindowsWithTitle("amine")
        if windows:
            flask_window = windows[0]
            getattr(flask_window, action.lower())()
            logger.info(f"Flask window {action}d.")
        else:
            logger.warning("Flask window not found.")
    except Exception as e:
        logger.error(f"Error {action}ing Flask window: {e}")


@app.route("/")
def index():
    return render_template("index.html", exit_combo=CONFIG["EXIT_COMBO"])


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/data")
def display_data():
    try:
        with sqlite3.connect("amine_data.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM sessions")
            sessions = c.fetchall()
            c.execute(
                "SELECT session_id, event_type, event_time FROM distractions ORDER BY event_time"
            )
            distractions = c.fetchall()
        return render_template(
            "data.html", sessions=sessions, distractions=distractions
        )
    except sqlite3.Error as e:
        logger.error(f"Error fetching data: {e}")
        return jsonify({"error": "Failed to fetch data"}), 500


@app.route("/start_pomodoro", methods=["POST"])
def start_pomodoro():
    try:
        data = request.json

        pomodoros = int(data["pomodoros"])
        focus_duration = int(data["focus_duration"])
        break_duration = int(data["break_duration"])
        link_type = data["link_type"]
        link = data["link"]

        threading.Thread(
            target=pomodoro_flow,
            args=(pomodoros, focus_duration, break_duration, link, link_type),
        ).start()

        logger.info("Pomodoro session started.")
        return jsonify({"status": "Pomodoro session started"})
    except Exception as e:
        logger.error(f"Error starting Pomodoro session: {e}")
        return jsonify({"status": "Error starting Pomodoro session"}), 500


@app.route("/session_graph")
def session_graph():
    conn = sqlite3.connect("amine_data.db")
    df = pd.read_sql_query("SELECT start_time, total_duration FROM sessions", conn)
    conn.close()

    plt.figure(figsize=(10, 5))
    plt.plot(pd.to_datetime(df["start_time"]), df["total_duration"], marker="o")
    plt.xlabel("Session Date")
    plt.ylabel("Duration (minutes)")
    plt.title("Pomodoro Session Durations")
    plt.grid(True)

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return send_file(img, mimetype="image/png")


@app.route("/distraction_graph")
def distraction_graph():
    conn = sqlite3.connect("amine_data.db")
    df = pd.read_sql_query("SELECT event_time, event_type FROM distractions", conn)
    conn.close()

    df["event_time"] = pd.to_datetime(df["event_time"])
    distractions_per_day = df.groupby(df["event_time"].dt.date).size()

    plt.figure(figsize=(10, 5))
    plt.bar(distractions_per_day.index, distractions_per_day.values)
    plt.xlabel("Date")
    plt.ylabel("Number of Distractions")
    plt.title("Distractions Over Time")
    plt.grid(True)

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return send_file(img, mimetype="image/png")


@app.route("/distraction_heatmap")
def distraction_heatmap():
    conn = sqlite3.connect("amine_data.db")
    df = pd.read_sql_query("SELECT event_time FROM distractions", conn)
    conn.close()

    if df.empty:
        return "No distraction data available."

    df["event_time"] = pd.to_datetime(df["event_time"])
    df["hour"] = df["event_time"].dt.hour
    df["day"] = df["event_time"].dt.date

    heatmap_data = df.pivot_table(
        index="day", columns="hour", aggfunc="size", fill_value=0
    )

    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap="coolwarm", cbar=True, linewidths=0.5)
    plt.title("Hourly Distractions Heatmap")
    plt.xlabel("Hour of Day")
    plt.ylabel("Date")

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return send_file(img, mimetype="image/png")


@app.route("/export_data")
def export_data():
    try:
        with sqlite3.connect("amine_data.db") as conn:

            sessions_df = pd.read_sql_query("SELECT * FROM sessions", conn)

            distractions_df = pd.read_sql_query("SELECT * FROM distractions", conn)

            combined_csv = pd.concat([sessions_df, distractions_df], axis=1)

            csv_data = combined_csv.to_csv(index=False)

            return send_file(
                BytesIO(csv_data.encode("utf-8")),
                mimetype="text/csv",
                as_attachment=True,
                download_name="session_distraction_data.csv",
            )
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({"error": "Failed to export data"}), 500


@app.route("/cumulative_focus_time")
def cumulative_focus_time():
    conn = sqlite3.connect("amine_data.db")
    df = pd.read_sql_query("SELECT start_time, total_duration FROM sessions", conn)
    conn.close()

    df["start_time"] = pd.to_datetime(df["start_time"])
    df["cumulative_duration"] = df["total_duration"].cumsum()

    fig = px.area(
        df,
        x="start_time",
        y="cumulative_duration",
        title="Cumulative Focus Time Over Sessions",
        labels={
            "start_time": "Session Start Time",
            "cumulative_duration": "Cumulative Duration (minutes)",
        },
    )

    img = BytesIO()
    fig.write_image(img, format="png")
    img.seek(0)
    return send_file(img, mimetype="image/png")


@app.route("/distraction_pie_chart")
def distraction_pie_chart():
    conn = sqlite3.connect("amine_data.db")
    df = pd.read_sql_query(
        "SELECT event_type, COUNT(*) as count FROM distractions GROUP BY event_type",
        conn,
    )
    conn.close()

    fig = px.pie(df, values="count", names="event_type", title="Types of Distractions")

    img = BytesIO()
    fig.write_image(img, format="png")
    img.seek(0)
    return send_file(img, mimetype="image/png")


def pomodoro_flow(pomodoros, focus_duration, break_duration, link, link_type):
    start_time = datetime.now()

    if link_type == "website":
        logger.info("Opening website.")
        webbrowser.open(link)
        manage_flask_window("minimize")
        time.sleep(5)
        pyautogui.click(x=100, y=200)
        pyautogui.press("f11")

    elif link_type == "file_path":
        logger.info("Opening file path.")
        open_window_titles = [win for win in gw.getAllTitles() if win]

        subprocess.run([link])

        try:
            new_win_title = [
                win
                for win in [i for i in gw.getAllTitles() if i]
                if win not in open_window_titles
            ][0]
            new_win_controller: gw.Window = gw.getWindowsWithTitle(new_win_title)[0]

            new_win_controller.maximize()
        except Exception as e:
            logger.error(f"Error opening application: {e}")
            notify_user("Error opening application. Please try again.")
            return

    with sqlite3.connect("amine_data.db") as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO sessions (start_time, end_time, total_duration) VALUES (?, ?, ?)",
            (start_time.strftime("%Y-%m-%d %H:%M:%S"), None, 0),
        )
        session_id = c.lastrowid

    focus_protection = FocusProtection(session_id=session_id)

    for i in range(pomodoros):
        winsound.Beep(500, 500)
        notify_user(f"Starting Pomodoro {i + 1}/{pomodoros}")
        logger.info(f"Starting Pomodoro {i + 1}/{pomodoros}")
        focus_protection.start_protection(focus_duration)

        if i < pomodoros - 1:
            winsound.Beep(500, 500)
            notify_user("Break time!")
            logger.info(f"Break: {break_duration} minutes")
            time.sleep(break_duration * 60)

    end_time = datetime.now()
    total_duration = focus_duration * pomodoros

    with sqlite3.connect("amine_data.db") as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE sessions SET end_time = ?, total_duration = ? WHERE id = ?",
            (end_time.strftime("%Y-%m-%d %H:%M:%S"), total_duration, session_id),
        )

    logger.info("Pomodoro session completed. Exiting fullscreen...")
    winsound.Beep(1000, 500)
    if link_type == "website":
        pyautogui.press("f11")
        manage_flask_window("maximize")
    elif link_type == "file_path":
        new_win_controller.minimize()
    notify_user("Pomodoro session completed.")
    logger.info("Flask window restored.")


if __name__ == "__main__":
    init_db()
    FlaskUI(app=app, server="flask", width=470, height=678).run()
