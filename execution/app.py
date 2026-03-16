"""
Module : app.py
Description : Serveur Flask — Interface web pour le Générateur de Fiches de Révision.
Point d'entrée principal du projet.

Usage  : python execution/app.py
Accès  : http://localhost:5001
"""

import os
import sys
import tempfile
import shutil

# Forcer l'encodage UTF-8 pour les logs Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Ajouter le dossier execution au path pour les imports relatifs
sys.path.insert(0, str(Path(__file__).parent))

# Charger les variables d'environnement depuis la racine du projet
load_dotenv(Path(__file__).parent.parent / ".env")

from pdf_analyzer import extraire_texte_pdf
from fiche_generator import generer_fiche_revision, valider_fiche
from drive_manager import copier_modele_vers_dossier
from google_docs_builder import remplir_google_doc, construire_nom_fichier

# --- Initialisation Flask ---
app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent.parent / "templates"),
    static_folder=str(Path(__file__).parent.parent / "templates" / "static"),
)
CORS(app)

# --- Configuration ---
PORT = int(os.getenv("PORT", 5001))
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", 200))
app.config["MAX_CONTENT_LENGTH"] = MAX_PDF_SIZE_MB * 1024 * 1024

# Dossier de logs/sorties temporaires
DOSSIER_SORTIES = Path(__file__).parent.parent / "sorties"
DOSSIER_SORTIES.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """Sert la page principale de l'interface."""
    return render_template("index.html")


@app.route("/api/generer", methods=["POST"])
def generer():
    """
    Pipeline principal : PDF → extraction → génération IA → création Google Doc.

    Formulaire attendu :
        intitule (str)  : Intitulé de la séance de formation
        date (str)      : Date de la session (YYYY-MM-DD)
        cursus (str)    : "Bachelor RH" ou "Mastère RH"
        pdf (file)      : Fichier PDF du support de formation

    Retourne:
        JSON: {
            "succes": bool,
            "etapes": list[dict],     → Progression étape par étape
            "lien_doc": str,          → Lien vers le Google Doc créé
            "nom_fichier": str,       → Nom du fichier créé
            "apercu_fiche": dict      → Aperçu de la fiche (premiers éléments)
        }
    """
    etapes = []

    # --- 1. Validation des données ---
    intitule = request.form.get("intitule", "").strip()
    date = request.form.get("date", "").strip()
    cursus = request.form.get("cursus", "Bachelor RH").strip()

    if not intitule:
        return jsonify({"succes": False, "erreur": "L'intitulé de la séance est requis."}), 400

    if not date:
        return jsonify({"succes": False, "erreur": "La date de la séance est requise."}), 400

    cursus_valides = ["Bachelor RH", "Mastère RH"]
    if cursus not in cursus_valides:
        cursus = "Bachelor RH"

    if "pdf" not in request.files or not request.files["pdf"].filename:
        return jsonify({"succes": False, "erreur": "Le fichier PDF du support est requis."}), 400

    pdf_file = request.files["pdf"]

    # --- 2. Sauvegarde temporaire du PDF ---
    temp_dir = Path(tempfile.mkdtemp())
    try:
        chemin_pdf_temp = temp_dir / "support_formation.pdf"
        pdf_file.save(str(chemin_pdf_temp))
        taille_kb = chemin_pdf_temp.stat().st_size // 1024
        etapes.append({
            "etape": "PDF reçu",
            "statut": "✅",
            "detail": f"{taille_kb} KB"
        })

        # --- 3. Extraction du contenu PDF ---
        print("🔍 Extraction du support de formation...")
        analyse = extraire_texte_pdf(str(chemin_pdf_temp))
        etapes.append({
            "etape": "Analyse PDF",
            "statut": "✅",
            "detail": f"{analyse['nb_pages']} pages, {len(analyse['sections'])} sections détectées"
        })

        contenu = analyse["contenu_complet"]

        if not contenu.strip():
            return jsonify({
                "succes": False,
                "erreur": "Impossible d'extraire du texte du PDF. Le fichier est peut-être scanné ou protégé.",
                "etapes": etapes
            }), 422

        # --- 4. Génération IA de la fiche ---
        print("🤖 Génération de la fiche de révision avec Gemini...")
        fiche_brute = generer_fiche_revision(contenu, intitule, cursus, date)
        fiche = valider_fiche(fiche_brute)

        nb_concepts = len(fiche.get("concepts_cles", []))
        nb_cas = len(fiche.get("cas_pratiques", []))
        etapes.append({
            "etape": "Fiche générée",
            "statut": "✅",
            "detail": f"{nb_concepts} concepts-clés, {nb_cas} cas pratique(s)"
        })

        # --- 5. Copie du modèle Google Doc ---
        print("📄 Copie du modèle Google Doc...")
        nom_fichier = construire_nom_fichier(cursus, intitule, date)
        doc_info = copier_modele_vers_dossier(nom_fichier)
        doc_id = doc_info["id"]
        etapes.append({
            "etape": "Google Doc créé",
            "statut": "✅",
            "detail": nom_fichier
        })

        # --- 6. Remplissage du Google Doc ---
        print("✍️  Remplissage du contenu dans le Google Doc...")
        remplir_google_doc(doc_id, fiche, intitule, date, cursus)
        etapes.append({
            "etape": "Contenu inséré",
            "statut": "✅",
            "detail": "Tous les champs remplis"
        })

        # --- Réponse finale ---
        apercu_fiche = {
            "objectifs": fiche.get("objectifs_seance", [])[:3],
            "concepts": fiche.get("concepts_cles", [])[:3],
            "points_essentiels": fiche.get("points_essentiels", [])[:5],
            "a_des_cas_pratiques": len(fiche.get("cas_pratiques", [])) > 0,
        }

        reponse = {
            "succes": True,
            "etapes": etapes,
            "lien_doc": doc_info["lien_web"],
            "nom_fichier": nom_fichier,
            "apercu_fiche": apercu_fiche,
        }
        print(f"✅ Fiche créée : {doc_info['lien_web']}")
        return jsonify(reponse)

    except Exception as e:
        etapes.append({"etape": "Erreur", "statut": "❌", "detail": str(e)})
        import traceback
        print(f"❌ Erreur : {e}")
        return jsonify({
            "succes": False,
            "erreur": str(e),
            "trace": traceback.format_exc(),
            "etapes": etapes
        }), 500

    finally:
        # Nettoyage du dossier temporaire
        shutil.rmtree(str(temp_dir), ignore_errors=True)


@app.route("/api/statut")
def statut():
    """Vérifie que le serveur et les dépendances sont opérationnels."""
    gemini_ok = bool(os.getenv("GEMINI_API_KEY"))
    sa_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
    sa_fichier = Path("./service_account.json").exists()

    if sa_env:
        drive_statut = "✅ Via variable d'environnement"
    elif sa_fichier:
        drive_statut = "✅ service_account.json présent"
    else:
        drive_statut = "❌ service_account.json manquant"

    statuts = {
        "serveur": "✅ En ligne",
        "gemini_api": "✅ Configurée" if gemini_ok else "❌ GEMINI_API_KEY manquante",
        "google_drive": drive_statut,
        "dossier_cible": os.getenv("DRIVE_FOLDER_FICHES", "Non configuré"),
        "modele_doc": os.getenv("DRIVE_MODELE_DOC_ID", "Non configuré"),
    }
    return jsonify(statuts)


# ─────────────────────────────────────────────
# Lancement
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  🎓 Générateur de Fiches de Révision")
    print("=" * 60)
    print(f"  Interface : http://localhost:{PORT}")
    print(f"  Statut    : http://localhost:{PORT}/api/statut")
    print("=" * 60)
    app.run(host="0.0.0.0", port=PORT, debug=False)
