
import os
from pathlib import Path
from dotenv import load_dotenv
import pickle
from googleapiclient.discovery import build

# Configuration des chemins
racine = Path(__file__).parent
load_dotenv(racine / ".env")

def obtenir_service_drive():
    creds = None
    token_path = racine / "token.pickle"
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    return build('drive', 'v3', credentials=creds)

def search_doc_version():
    service = obtenir_service_drive()
    query = "name contains 'MODELE CAHIER DE TEXTE' and mimeType = 'application/vnd.google-apps.document'"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])
    
    if not files:
        print("Aucune version Google Docs trouvée.")
    else:
        print("Versions Google Docs trouvées :")
        for f in files:
            print(f"- Nom: {f['name']}, ID: {f['id']}")

if __name__ == "__main__":
    search_doc_version()
