"""
Entrée Vercel — Sert l'application Flask en mode serverless.
Ce fichier est le point d'entrée pour Vercel (dossier api/).
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier execution au path Python
sys.path.insert(0, str(Path(__file__).parent.parent / "execution"))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Importer l'application Flask depuis execution/app.py
from app import app

# Handler Vercel
handler = app
