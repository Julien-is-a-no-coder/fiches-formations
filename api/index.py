import sys
import os
from pathlib import Path

# Ajouter la racine du projet au path Python pour permettre les imports absolus
ROOT = str(Path(__file__).parent.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Importer l'application Flask
try:
    from execution.app import app
except ImportError as e:
    print(f"Erreur d'importation : {e}")
    # Fallback pour tenter l'import direct si le path est différent
    sys.path.insert(0, os.path.join(ROOT, "execution"))
    from app import app

# Vercel utilise 'app' par défaut, on l'expose
handler = app
app = app
