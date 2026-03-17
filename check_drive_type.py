
import os
from pathlib import Path
from dotenv import load_dotenv
import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Configuration des chemins
racine = Path(__file__).parent
load_dotenv(racine / ".env")

def obtenir_service_drive():
    creds = None
    token_path = racine / "token.pickle"
    creds_path = racine / "credentials.json"
    
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Token invalide ou inexistant")

    return build('drive', 'v3', credentials=creds)

def check_file(file_id):
    service = obtenir_service_drive()
    try:
        file = service.files().get(fileId=file_id, fields='name, mimeType').execute()
        print(f"Fichier: {file['name']}")
        print(f"MimeType: {file['mimeType']}")
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    # ID du doc qui a échoué
    target_id = "1xEmKKAd6Rphw30sDr20Wlp6U3KvzM9SC"
    check_file(target_id)
    
    # ID du modèle (depuis .env)
    modele_id = os.getenv("DRIVE_MODELE_DOC_ID")
    print(f"\nModèle ID: {modele_id}")
    if modele_id:
        check_file(modele_id)
