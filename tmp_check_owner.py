import os
import sys
from pathlib import Path

# Ajouter execution au path
sys.path.insert(0, str(Path("execution").resolve()))

from drive_manager import obtenir_service_drive, FOLDER_FICHES

def check_owner():
    service = obtenir_service_drive()
    print(f"FOLDER_FICHES: {FOLDER_FICHES}")
    folder = service.files().get(fileId=FOLDER_FICHES, fields="id, name, owners").execute()
    owners = folder.get('owners', [])
    for o in owners:
        print(f"Owner: {o.get('displayName')} ({o.get('emailAddress')})")
    
    # Check self
    about = service.about().get(fields="user, storageQuota").execute()
    print(f"Me (Authenticated): {about.get('user', {}).get('emailAddress')}")
    q = about.get('storageQuota', {})
    print(f"Usage: {q.get('usage', 'No usage')} / {q.get('limit', 'Unlimited')}")

if __name__ == "__main__":
    check_owner()
