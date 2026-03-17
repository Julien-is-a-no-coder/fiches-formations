import os
from pathlib import Path
from dotenv import load_dotenv

import sys
sys.path.insert(0, str(Path("execution").resolve()))

from google_docs_builder import remplir_docx_local

fiche_test = {
    "objectifs_seance": ["Objectif 1"],
    "concepts_cles": [{"terme": "Terme 1", "definition": "Def"}],
    "synthese_contenu": "Ceci est une synthèse abrégée",
    "points_essentiels": ["Point 1"],
    "ressources_pedagogiques": ["Ressource 1"],
    "cas_pratiques": [{"titre": "Cas 1", "description": "Desc", "consigne": "Cons"}],
    "points_vigilance": ["Vigil 1"],
    "deroule_pedagogique": "Déroulé bref"
}

remplir_docx_local("test.docx", "test_out.docx", fiche_test, "Test Intitulé", "2026-03-16", "Bachelor RH")

print(f"File size before python-docx: {os.path.getsize('test.docx')}")
print(f"File size after python-docx: {os.path.getsize('test_out.docx')}")
