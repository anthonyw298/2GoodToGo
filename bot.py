import json
import math
import time
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from auth import get_client, save_client_tokens
from notifier import notify

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

POLL_FASTEST = 0.2  # seconds between polls at peak (center of window)
POLL_SLOWEST = 3.0  # seconds between polls at edges of window
WINDOW = 30         # seconds before/after target time to poll
MAX_CALLS = 180     # hard cap per window — bot stops polling after this


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"jobs": []}


def in_window(time_str):
    """True if now is within ±WINDOW seconds of the target time."""
    now = datetime.now()
    try:
        h, m = map(int, time_str.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        return abs((now - target).total_seconds()) <= WINDOW
    except ValueError:
        return False


def seconds_until(time_str):
    """Seconds until the start of the next polling window."""
    now = datetime.now()
    try:
        h, m = map(int, time_str.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        start = target - timedelta(seconds=WINDOW)

        if now > target + timedelta(seconds=WINDOW):
            start += timedelta(days=1)

        return max(0, (start - now).total_seconds())
    except ValueError:
        return 3600


def poll_interval(time_str):
    """Return poll interval using a normal distribution centered on target time.
    Fastest at center, slowest at edges."""
    now = datetime.now()
    try:
        h, m = map(int, time_str.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        offset = abs((now - target).total_seconds())

        # Gaussian: e^(-(x^2)/(2*sigma^2)), sigma = WINDOW/3 so edges ≈ 0
        sigma = WINDOW / 3
        weight = math.exp(-(offset ** 2) / (2 * sigma ** 2))

        # weight=1 at center → POLL_FASTEST, weight≈0 at edges → POLL_SLOWEST
        interval = POLL_SLOWEST - weight * (POLL_SLOWEST - POLL_FASTEST)
        return interval + random.uniform(0, 0.1)
    except ValueError:
        return POLL_SLOWEST


def try_buy(client, job, dry_run=False):
    """Check availability and purchase if possible. Returns True on success."""
    item_id = job["item_id"]
    store = job["store_name"]
    qty = job.get("quantity", 1)
    ts = datetime.now().strftime("%H:%M:%S")

    try:
        item = client.get_item(item_id=item_id)
        available = item.get("items_available", 0)

        if available > 0:
            if dry_run:
                print(f"  [{ts}] {store} — {available} bag(s) found! [TEST MODE — not purchasing]")
                notify("2GoodToGo - TEST", f"Would have bought {qty}x bag at {store}.")
                return True
            print(f"  [{ts}] {store} — {available} bag(s) found! Purchasing...")
            order = client.create_order(item_id=item_id, item_count=qty)
            notify(
                "2GoodToGo - Bag Reserved!",
                f"Got {qty}x bag at {store}. Open TGTG app for pickup details.",
            )
            return True
        else:
            print(f"  [{ts}] {store} — no bags yet", end="\r")
            return False

    except Exception as e:
        err = str(e).lower()
        if "429" in err or "rate" in err or "too many" in err:
            print(f"  [{ts}] {store} — rate limited, backing off 10s")
            time.sleep(10)
        else:
            print(f"  [{ts}] {store} — error: {e}")
        return False


def main():
    dry_run = "--test" in sys.argv

    print("=" * 50)
    print("  2GoodToGo Bot" + (" [TEST MODE]" if dry_run else ""))
    print("=" * 50)
    if dry_run:
        print("\n  Test mode: will poll but NOT purchase.\n")

    client = get_client()
    print("Bot is running. Press Ctrl+C to stop.\n")

    purchased_today = set()
    current_date = datetime.now().date()
    call_counts = {}  # job_id -> calls made this window

    # Save refreshed tokens periodically
    last_token_save = time.time()

    try:
        while True:
            # Reset purchases at midnight
            today = datetime.now().date()
            if today != current_date:
                purchased_today.clear()
                call_counts.clear()
                current_date = today

            config = load_config()
            jobs = [
                j for j in config.get("jobs", [])
                if j.get("enabled", True) and j["id"] not in purchased_today
            ]

            if not jobs:
                print("No active jobs. Add one: python manage.py add")
                time.sleep(30)
                continue

            # Check all active windows
            bought_any = False
            for job in jobs:
                if not in_window(job["time"]):
                    # Reset count when outside window
                    call_counts.pop(job["id"], None)
                    continue

                # Enforce hard cap
                count = call_counts.get(job["id"], 0)
                if count >= MAX_CALLS:
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"  [{ts}] {job['store_name']} — hit {MAX_CALLS} call limit, waiting for next window")
                    continue

                if try_buy(client, job, dry_run=dry_run):
                    purchased_today.add(job["id"])
                    bought_any = True
                else:
                    call_counts[job["id"]] = count + 1

            if bought_any:
                continue

            # If any job is in window and under limit, poll with bell curve timing
            active_jobs = [
                j for j in jobs
                if in_window(j["time"]) and call_counts.get(j["id"], 0) < MAX_CALLS
            ]
            if active_jobs:
                # Use the fastest interval among active jobs
                interval = min(poll_interval(j["time"]) for j in active_jobs)
                time.sleep(interval)
            else:
                # Sleep until next window
                wait = min(seconds_until(j["time"]) for j in jobs)
                if wait > 120:
                    mins = int(wait / 60)
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"  [{ts}] Next job in ~{mins} min. Sleeping...")
                    time.sleep(min(wait - 30, 300))
                else:
                    time.sleep(1)

            # Save tokens every 30 minutes
            if time.time() - last_token_save > 1800:
                try:
                    save_client_tokens(client)
                except Exception:
                    pass
                last_token_save = time.time()

    except KeyboardInterrupt:
        print("\n\nBot stopped.")
        try:
            save_client_tokens(client)
        except Exception:
            pass


if __name__ == "__main__":
    main()
