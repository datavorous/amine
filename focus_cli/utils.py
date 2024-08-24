from tqdm import tqdm
import time

def countdown_timer(seconds):
    """Countdown timer for the specified number of seconds."""
    for remaining in tqdm(range(seconds), desc=f"Time left", bar_format="{l_bar}{bar} | {remaining}s left"):
        time.sleep(1)
