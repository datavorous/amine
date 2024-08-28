from flask import Flask, render_template, request, jsonify
from flaskwebgui import FlaskUI
import threading
import webbrowser
from datetime import datetime, timedelta
import pyautogui
import keyboard
import time
import sys
import pygetwindow as gw
import winsound
#from win11toast import toast

app = Flask(__name__)

CONFIG = {
    "SAFE_X": 500,
    "SAFE_Y": 500,
    "TOP_SCREEN_THRESHOLD": 40,
    "BLOCKED_KEYS": [
        'left windows', 'right windows', 'alt', 'tab', 'ctrl', 'esc', 
        'f11', 'cmd', 'command', 'win'
    ],
    "EXIT_COMBO": 'ctrl+shift+q',
    "MOUSE_ENFORCE_DELAY": 0.08  # Configurable delay for mouse boundary enforcement
}

class FocusProtection:
    def __init__(self, config=CONFIG):
        self.config = config
        pyautogui.FAILSAFE = False
        self.protection_active = False
        self.mouse_thread = None
        #self.quit_early = False  # Flag to track early quit

    def enforce_mouse_boundaries(self):
        screen_width, screen_height = pyautogui.size()
        while self.protection_active:
            x, y = pyautogui.position()
            if (y < self.config["TOP_SCREEN_THRESHOLD"] or y > screen_height - self.config["TOP_SCREEN_THRESHOLD"]):
                pyautogui.moveTo(self.config["SAFE_X"], self.config["SAFE_Y"])
            time.sleep(self.config["MOUSE_ENFORCE_DELAY"])

    def block_keys(self):
        for key in self.config["BLOCKED_KEYS"]:
            keyboard.block_key(key)

    def unblock_keys(self):
        keyboard.unhook_all()

    def safe_exit(self):
        self.unblock_keys()
        sys.exit(0)

    def block_distractions(self, duration_minutes):
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        self.block_keys()
        self.protection_active = True
        self.mouse_thread = threading.Thread(target=self.enforce_mouse_boundaries, daemon=True)
        self.mouse_thread.start()

        try:
            while datetime.now() < end_time:
                if keyboard.is_pressed(self.config["EXIT_COMBO"]):
                    self.safe_exit()
                time.sleep(0.1)
        finally:
            self.protection_active = False
            self.mouse_thread.join()
            self.unblock_keys()

    def start_protection(self, duration_minutes):
        self.block_distractions(duration_minutes)

def minimize_flask_window():
    print("Minimizing Flask window...")
    windows = gw.getWindowsWithTitle("amine")  
    if windows:
        flask_window = windows[0]
        flask_window.minimize()
        print("Flask window minimized.")
    else:
        print("Flask window not found.")

def maximize_flask_window():
    print("Maximizing Flask window...")
    windows = gw.getWindowsWithTitle("amine")  
    if windows:
        flask_window = windows[0]
        flask_window.maximize()
        print("Flask window maximized.")
    else:
        print("Flask window not found.")


"""
def get_browser_window():
    possible_browsers = ['Google Chrome', 'Mozilla Firefox', 'Microsoft Edge', 'Brave', 'Opera', 'Safari']  # Add more as needed
    for browser in possible_browsers:
        windows = gw.getWindowsWithTitle(browser)
        if windows:
            return windows[0]  # Return the first match found
    return None

def ensure_fullscreen():
    pass
    print("Ensuring fullscreen mode...")
    browser_window = get_browser_window()
    if browser_window:
        if not browser_window.isMaximized:  # Maximize window first
            print(f"Maximizing {browser_window.title} window...")
            browser_window.maximize()
            time.sleep(1)
            pyautogui.press('f11')  # Toggle fullscreen mode
            time.sleep(2)
            if browser_window.isFullscreen:
                print("Fullscreen mode applied successfully.")
            else:
                print("Failed to apply fullscreen mode.")
        else:
            print(f"{browser_window.title} window is already fullscreen.")
    else:
        print("No browser window found.")"""


@app.route('/')
def index():
    return render_template('index.html', exit_combo=CONFIG['EXIT_COMBO'])

@app.route('/start_pomodoro', methods=['POST'])
def start_pomodoro():
    pomodoros = int(request.form['pomodoros'])
    focus_duration = int(request.form['focus_duration'])
    break_duration = int(request.form['break_duration'])
    website = request.form['website']

    threading.Thread(target=pomodoro_flow, args=(pomodoros, focus_duration, break_duration, website)).start()

    return jsonify({'status': 'Pomodoro session started'})

def pomodoro_flow(pomodoros, focus_duration, break_duration, website):
    

    webbrowser.open(website)
    minimize_flask_window()
    time.sleep(5) # Adjust timing as necessary
    pyautogui.click(x=100, y=200)  
    # this is some kind of jugad i presume
    # ensure_fullscreen()  # This implementation failed. It Ensured the window is fullscreen
    
    pyautogui.press('f11')  

    focus_protection = FocusProtection()
    #winsound.Beep(500,500)
    for i in range(pomodoros):
        winsound.Beep(500,500)
        print(f"Starting Pomodoro {i + 1}/{pomodoros}")
        focus_protection.start_protection(focus_duration)

        if i < pomodoros - 1:
            winsound.Beep(500,500)
            print(f"Break: {break_duration} minutes")
            time.sleep(break_duration * 60)

    print("Pomodoro session completed. Exiting fullscreen...")
    winsound.Beep(1000,500)
    pyautogui.press('f11')  # Exit fullscreen
    maximize_flask_window()
    print("Flask window restored.")



if __name__ == '__main__':
    FlaskUI(app=app, server="flask",width=470, height=628,).run()
