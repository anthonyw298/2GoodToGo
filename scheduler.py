import sys
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent


def install():
    """Add bot to Windows Task Scheduler to run at login."""
    python = sys.executable
    bot = BASE_DIR / "bot.py"

    if os.name == "nt":
        subprocess.run(
            [
                "schtasks", "/create",
                "/tn", "2GoodToGo",
                "/tr", f'"{python}" "{bot}"',
                "/sc", "onlogon",
                "/rl", "limited",
                "/f",
            ],
            check=True,
        )
        print("Done! Bot will auto-start when you log in.")
        print("To remove: python scheduler.py uninstall")
    else:
        print("Windows only. On Mac just run: python bot.py")


def uninstall():
    """Remove the auto-start task."""
    if os.name == "nt":
        subprocess.run(
            ["schtasks", "/delete", "/tn", "2GoodToGo", "/f"],
            check=True,
        )
        print("Auto-start removed.")
    else:
        print("Nothing to remove on this platform.")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("install", "uninstall"):
        print("Usage: python scheduler.py <install|uninstall>")
        print("\n  install    Start bot automatically on Windows login")
        print("  uninstall  Remove auto-start")
        return

    {"install": install, "uninstall": uninstall}[sys.argv[1]]()


if __name__ == "__main__":
    main()
