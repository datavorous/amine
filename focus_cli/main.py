import sys
from focus_cli.cli import pomodoro

def main():
    try:
        pomodoro(standalone_mode=False)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()
