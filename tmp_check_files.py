import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ajouter execution au path
sys.path.insert(0, str(Path("execution").resolve()))

from drive_manager import obtenir_service_drive, FOLDER_FICHES

def list_recent_files():
    service = obtenir_service_drive()
    print(f"FOLDER_FICHES: {FOLDER_FICHES}")
    results = service.files().list(
        q=f"'{FOLDER_FICHES}' in parents and trashed = false",
        fields="files(id, name, createdTime)",
        pageSize=5,
        orderBy="createdTime desc"
    ).execute()
    files = results.get('files', [])
    for f in files:
        print(f"{f['createdTime']} - {f['name']} ({f['id']})")

if __name__ == "__main__":
    list_recent_files()
