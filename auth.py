import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from tgtg import TgtgClient

load_dotenv()

BASE_DIR = Path(__file__).parent
TOKENS_FILE = BASE_DIR / "tokens.json"


def save_tokens(credentials):
    TOKENS_FILE.write_text(json.dumps(credentials, indent=2))
    try:
        TOKENS_FILE.chmod(0o600)
    except OSError:
        pass


def load_tokens():
    if TOKENS_FILE.exists():
        return json.loads(TOKENS_FILE.read_text())
    return None


def get_client():
    tokens = load_tokens()
    if not tokens:
        print("Not logged in. Run: python auth.py")
        sys.exit(1)
    return TgtgClient(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user_id=tokens["user_id"],
        cookie=tokens.get("cookie", ""),
    )


def save_client_tokens(client):
    tokens = {
        "access_token": client.access_token,
        "refresh_token": client.refresh_token,
        "user_id": client.user_id,
        "cookie": getattr(client, "cookie", ""),
    }
    save_tokens(tokens)


def login():
    email = os.getenv("TGTG_EMAIL")
    if not email:
        email = input("Enter your TGTG email: ").strip()

    print(f"\nSending login email to {email}...")
    print("Check your inbox and click the login link, then come back here.\n")

    client = TgtgClient(email=email)
    credentials = client.get_credentials()
    save_tokens(credentials)
    print("Login successful! Tokens saved.\n")
    return client


if __name__ == "__main__":
    login()
