import json
import sys
import requests
from pathlib import Path
from auth import get_client

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"jobs": []}


def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def next_id(config):
    ids = [j["id"] for j in config.get("jobs", [])]
    return max(ids, default=0) + 1


def geocode(query):
    """Convert location string to lat/lon using OpenStreetMap (free, no key)."""
    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1},
        headers={"User-Agent": "2GoodToGo-Bot/1.0"},
        timeout=10,
    )
    results = resp.json()
    if results:
        return float(results[0]["lat"]), float(results[0]["lon"])
    return None, None


def format_price(price_info):
    minor = price_info.get("minor_units", 0)
    decimals = price_info.get("decimals", 2)
    code = price_info.get("code", "USD")
    amount = minor / (10 ** decimals)
    if code == "USD":
        return f"${amount:.2f}"
    return f"{amount:.2f} {code}"


def display_items(items):
    print(f"\n  {'#':<4} {'Store':<35} {'Price':<10} {'Available'}")
    print(f"  {'---':<4} {'---':<35} {'---':<10} {'---':<10}")
    for i, item in enumerate(items, 1):
        name = item.get("store", {}).get("store_name", "Unknown")[:35]
        price = format_price(
            item.get("item", {}).get("price_including_taxes", {})
        )
        avail = item.get("items_available", 0)
        print(f"  {i:<4} {name:<35} {price:<10} {avail}")


def add_job():
    client = get_client()

    print("\nHow would you like to find your store?")
    print("  1. Search by location")
    print("  2. Browse your TGTG favorites")
    print("  3. Enter item ID directly")

    choice = input("\n> ").strip()
    items = []

    if choice == "1":
        location = input("\nEnter a location (city, address, etc.): ").strip()
        lat, lon = geocode(location)
        if not lat:
            print("Could not find that location.")
            return
        print(f"\nSearching near {location}...")
        items = client.get_items(
            favorites_only=False, latitude=lat, longitude=lon,
            radius=5, page_size=20, page=1,
        )

    elif choice == "2":
        print("\nLoading your favorites...")
        items = client.get_items(favorites_only=True)

    elif choice == "3":
        item_id = input("\nEnter the item ID: ").strip()
        time_str = input("What time do bags usually drop? (HH:MM, 24h): ").strip()
        qty = input("Quantity [1]: ").strip() or "1"

        config = load_config()
        job = {
            "id": next_id(config),
            "item_id": item_id,
            "store_name": f"Store #{item_id}",
            "time": time_str,
            "quantity": int(qty),
            "enabled": True,
        }
        config["jobs"].append(job)
        save_config(config)
        print(f"\nAdded job #{job['id']}. Run the bot: python bot.py")
        return

    else:
        print("Invalid choice.")
        return

    if not items:
        print("No stores found.")
        return

    display_items(items)

    try:
        idx = int(input("\nSelect store (number): ").strip()) - 1
        selected = items[idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    item_id = str(selected["item"]["item_id"])
    store_name = selected["store"]["store_name"]
    address = (
        selected.get("store", {})
        .get("store_location", {})
        .get("address", {})
        .get("address_line", "")
    )

    time_str = input("\nWhat time do bags usually drop? (HH:MM, 24h): ").strip()
    qty = input("Quantity [1]: ").strip() or "1"

    config = load_config()
    job = {
        "id": next_id(config),
        "item_id": item_id,
        "store_name": store_name,
        "address": address,
        "time": time_str,
        "quantity": int(qty),
        "enabled": True,
    }
    config["jobs"].append(job)
    save_config(config)

    print(f"\nAdded job #{job['id']}:")
    print(f"  Store:    {store_name}")
    if address:
        print(f"  Address:  {address}")
    print(f"  Time:     {time_str} (polls ±1 min)")
    print(f"  Quantity: {qty}")
    print(f"\nRun the bot: python bot.py")


def list_jobs():
    config = load_config()
    jobs = config.get("jobs", [])

    if not jobs:
        print("\nNo jobs configured. Run: python manage.py add")
        return

    print(f"\n  {'ID':<4} {'Store':<30} {'Time':<8} {'Qty':<5} {'Status'}")
    print(f"  {'--':<4} {'--':<30} {'--':<8} {'--':<5} {'--':<10}")
    for j in jobs:
        status = "ON" if j.get("enabled", True) else "OFF"
        print(
            f"  {j['id']:<4} {j['store_name'][:30]:<30} "
            f"{j['time']:<8} {j['quantity']:<5} {status}"
        )


def edit_job():
    config = load_config()
    jobs = config.get("jobs", [])

    if not jobs:
        print("\nNo jobs to edit.")
        return

    list_jobs()
    target = input("\nEnter job ID to edit: ").strip()

    job = next((j for j in jobs if str(j["id"]) == target), None)
    if not job:
        print("Job not found.")
        return

    print(f"\nEditing job #{job['id']} — {job['store_name']}")
    print("Press Enter to keep current value.\n")

    new_time = input(f"  Time [{job['time']}]: ").strip()
    if new_time:
        job["time"] = new_time

    new_qty = input(f"  Quantity [{job['quantity']}]: ").strip()
    if new_qty:
        job["quantity"] = int(new_qty)

    toggle = input(f"  Enabled [{'yes' if job.get('enabled', True) else 'no'}] (y/n): ").strip().lower()
    if toggle == "y":
        job["enabled"] = True
    elif toggle == "n":
        job["enabled"] = False

    save_config(config)
    print(f"\nJob #{job['id']} updated.")


def delete_job():
    config = load_config()
    jobs = config.get("jobs", [])

    if not jobs:
        print("\nNo jobs to delete.")
        return

    list_jobs()
    target = input("\nEnter job ID to delete: ").strip()

    before = len(jobs)
    config["jobs"] = [j for j in jobs if str(j["id"]) != target]

    if len(config["jobs"]) == before:
        print("Job not found.")
        return

    save_config(config)
    print(f"\nJob #{target} deleted.")


def main():
    commands = {
        "add": add_job,
        "list": list_jobs,
        "edit": edit_job,
        "delete": delete_job,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("\nUsage: python manage.py <command>")
        print("\n  add      Add a store to watch")
        print("  list     List all jobs")
        print("  edit     Edit a job")
        print("  delete   Delete a job")
        return

    commands[sys.argv[1]]()


if __name__ == "__main__":
    main()
