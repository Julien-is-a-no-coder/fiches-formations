import os
from pathlib import Path
from dotenv import load_dotenv

import sys
sys.path.insert(0, str(Path("execution").resolve()))

from drive_manager import uploader_vers_drive_et_convertir

print("Uploading test_out.docx...")
result = uploader_vers_drive_et_convertir("test_out.docx", "Test Upload 2")
print(result)
