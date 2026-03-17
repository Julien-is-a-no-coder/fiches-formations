import base64
import json
from pathlib import Path

def generer_secrets():
    print("--- Preparation des secrets pour Vercel ---")
    
    # 1. Token Pickle -> Base64
    token_path = Path("token.pickle")
    if token_path.exists():
        with open(token_path, "rb") as f:
            b64_token = base64.b64encode(f.read()).decode("utf-8")
            print("\nGOOGLE_TOKEN_PICKLE_BASE64 (copier dans Vercel) :")
            print(b64_token)
    else:
        print("\nERREUR : token.pickle non trouve.")

    # 2. Credentials JSON -> string
    creds_path = Path("credentials.json")
    if creds_path.exists():
        with open(creds_path, "r") as f:
            creds_data = f.read()
            print("\nGOOGLE_CREDENTIALS_JSON_CONTENT (copier dans Vercel) :")
            print(creds_data)
    else:
        print("\nERREUR : credentials.json non trouve.")

if __name__ == "__main__":
    generer_secrets()
