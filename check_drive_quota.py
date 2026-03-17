import os
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'env
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive"]

def check_quota():
    print("[LOG] Verification du quota Google Drive...")
    
    # 1. Obtenir les credentials
    sa_json_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
    if sa_json_env:
        print("[INFO] Utilisation du Service Account (depuis ENV)")
        sa_info = json.loads(sa_json_env)
        creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    else:
        sa_path = Path("./service_account.json")
        if sa_path.exists():
            print(f"[INFO] Utilisation du fichier {sa_path}")
            creds = service_account.Credentials.from_service_account_file(str(sa_path), scopes=SCOPES)
        else:
            print("[ERROR] Aucun Service Account trouvé.")
            return

    service = build("drive", "v3", credentials=creds)

    # 2. Récupérer les infos du quota
    try:
        about = service.about().get(fields="storageQuota, user").execute()
        quota = about.get("storageQuota", {})
        user = about.get("user", {})
        
        limit = int(quota.get("limit", 0))
        usage = int(quota.get("usage", 0))
        
        print(f"\n[USER] Compte : {user.get('emailAddress')}")
        print(f"[DATA] Usage  : {usage / (1024**2):.2f} MB")
        if limit > 0:
            print(f"[DATA] Limite : {limit / (1024**2):.2f} MB")
            print(f"[DATA] Libre  : {(limit - usage) / (1024**2):.2f} MB")
            print(f"[WARN] Pourcentage utilise : {(usage / limit) * 100:.2f}%")
        else:
            print("[DATA] Limite : Illimitee")

        if usage >= limit and limit > 0:
            print("\n[ALERT] Le quota est effectivement depasse !")
            
        # 3. Lister quelques fichiers volumineux ou récents pour voir
        print("\n[FILES] Top 5 des fichiers recents du Service Account :")
        results = service.files().list(
            pageSize=5, 
            fields="files(id, name, size, mimeType, createdTime)",
            orderBy="createdTime desc"
        ).execute()
        files = results.get("files", [])
        for f in files:
            size = int(f.get('size', 0)) / 1024 if f.get('size') else 0
            print(f"  - {f['name']} ({f['mimeType']}) - {size:.1f} KB - Cree le {f['createdTime']}")

    except Exception as e:
        print(f"[ERROR] Erreur lors de la verification : {e}")

if __name__ == "__main__":
    check_quota()
