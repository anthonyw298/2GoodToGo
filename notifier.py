import platform


def notify(title, message):
    """Send a desktop notification with console fallback."""
    print(f"\n*** [{title}] {message} ***\n")

    try:
        system = platform.system()
        if system == "Windows":
            from plyer import notification
            notification.notify(title=title, message=message, timeout=10)
        elif system == "Darwin":
            import subprocess
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{message}" with title "{title}"'],
                check=False,
            )
    except Exception:
        pass
