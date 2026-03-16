import os
import sys
from pathlib import Path

# On ajoute le dossier racine et le dossier execution au path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "execution"))

# On importe l'application Flask
# Vercel cherche une variable nommée 'app' dans api/index.py
from execution.app import app as application

# On l'expose pour Vercel
app = application
