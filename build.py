import PyInstaller.__main__
import os

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.dirname(__file__))

# Path to the main script
main_script = os.path.join(project_root, "focus_cli", "main.py")

# Run PyInstaller
PyInstaller.__main__.run([
    main_script,
    "--onefile",
    "--name=focus",
    "--add-data=focus_cli;focus_cli",
    "--hidden-import=focus_cli.cli",
    "--hidden-import=focus_cli.focus_protection",
    "--hidden-import=focus_cli.config",
    "--hidden-import=focus_cli.utils",
    "--console",
])