import os
from pathlib import Path
from dotenv import load_dotenv

# Load execution directory to python path
import sys
sys.path.insert(0, str(Path("execution").resolve()))

from drive_manager import MODELE_DOC_ID, obtenir_service_drive, FOLDER_FICHES
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io

load_dotenv()
service = obtenir_service_drive()

def test_download_and_upload():
    print("Testing download...")
    fh = io.BytesIO()
    try:
        request = service.files().get_media(fileId=MODELE_DOC_ID)
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")
    except Exception as e:
        print(f"Failed get_media, trying export_media... {e}")
        request = service.files().export_media(
            fileId=MODELE_DOC_ID,
            mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

    doc_data = fh.getvalue()
    print(f"Downloaded {len(doc_data)} bytes.")
    
    with open("test.docx", "wb") as f:
        f.write(doc_data)
        
    print("Uploading...")
    metadata = {
        "name": "Test Upload",
        "parents": [FOLDER_FICHES],
        "mimeType": "application/vnd.google-apps.document"
    }

    media = MediaFileUpload(
        "test.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        resumable=False
    )

    fichier = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,name,webViewLink"
    ).execute()
    
    print(fichier)

test_download_and_upload()
