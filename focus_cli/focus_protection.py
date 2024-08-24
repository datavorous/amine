import pyautogui
import keyboard
import time
import ctypes
import os
import threading
from datetime import datetime, timedelta
import winsound
from tqdm import tqdm
from .config import CONFIG


class FocusProtection:
    def __init__(self, config=CONFIG):
        self.config = config
        pyautogui.FAILSAFE = False

    def hide_console(self):
        """Hide the console window."""
        # Optional: Hide the console window if needed, commented for safety
        # ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        pass

    def enforce_mouse_boundaries(self):
        """Continuously enforce mouse boundaries."""
        screen_width, screen_height = pyautogui.size()
        while True:
            x, y = pyautogui.position()
            if (y < self.config["TOP_SCREEN_THRESHOLD"] or 
                x == 0 or x == screen_width - 1 or y == screen_height - 1):
                pyautogui.moveTo(self.config["SAFE_X"], self.config["SAFE_Y"])
            time.sleep(0.08)

    def block_keys(self):
        """Block specified keys."""
        for key in self.config["BLOCKED_KEYS"]:
            keyboard.block_key(key)

    def unblock_keys(self):
        """Unblock all keys."""
        keyboard.unhook_all()

    def safe_exit(self):
        """Perform a safe exit."""
        self.unblock_keys()
        os._exit(0)

    def block_distractions(self, end_time):
        """Block distractions until the specified end time."""
        self.block_keys()
        while datetime.now() < end_time:
            if keyboard.is_pressed(self.config["EXIT_COMBO"]):
                self.safe_exit()
            time.sleep(0.1)

    def start_protection(self, duration_minutes):
        """Start the focus protection for the specified duration."""
        self.hide_console()
        self.enter_fullscreen()

        # Alert user with a beep sound
        winsound.Beep(1000, 500)
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        # Start mouse boundary enforcement
        threading.Thread(target=self.enforce_mouse_boundaries, daemon=True).start()

        # Block distractions during the focus session
        self.block_distractions(end_time)

        # Signal session completion with a beep
        winsound.Beep(1000, 1000)
        
        # Exit fullscreen mode at the end
        self.exit_fullscreen()

        # Unblock the keys at the end of the session
        self.unblock_keys()

    @staticmethod
    def enter_fullscreen():
        """Enter fullscreen mode."""
        pyautogui.press('f11')

    @staticmethod
    def exit_fullscreen():
        """Exit fullscreen mode."""
        pyautogui.press('f11')
