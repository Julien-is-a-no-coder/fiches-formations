import pickle
from pathlib import Path

def check_token():
    if Path("token.pickle").exists():
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)
            print(f"Token valid: {creds.valid}")
            print(f"Expired: {creds.expired}")
            print(f"Scopes: {creds.scopes}")
            if hasattr(creds, 'refresh_token') and creds.refresh_token:
                print("Refresh token present: ✅")
            else:
                print("Refresh token present: ❌")
    else:
        print("token.pickle not found.")

if __name__ == "__main__":
    check_token()
