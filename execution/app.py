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

# Configuration des logs
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
from drive_manager import (
    verifier_connexion, telecharger_modele, uploader_vers_drive_et_convertir,
    vider_corbeille, nettoyer_dossier_fiches
)
from google_docs_builder import (
    construire_nom_fichier, remplir_docx_local
)

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
# Sur Vercel, seul /tmp est accessible en écriture
if os.environ.get("VERCEL"):
    DOSSIER_SORTIES = Path("/tmp")
else:
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
    """Pipeline principal : PDF → extraction → génération IA → création Google Doc."""
    print("\n🚀 [V2] Démarrage de la génération (Méthode Local Processing)...")
    etapes = []

    # --- 1. Validation des données ---
    intitule = request.form.get("intitule", "").strip()
    date = request.form.get("date", "").strip()
    cursus = request.form.get("cursus", "Bachelor RH").strip()
    duree = request.form.get("duree", "Demie journée").strip()

    if not intitule:
        return jsonify({"succes": False, "erreur": "L'intitulé de la séance est requis."}), 400

    if not date:
        return jsonify({"succes": False, "erreur": "La date de la séance est requise."}), 400

    cursus_valides = ["Bachelor RH", "Mastère RH", "Formation continue"]
    if cursus not in cursus_valides:
        cursus = "Bachelor RH"

    duree_valides = ["Demie journée", "Journée"]
    if duree not in duree_valides:
        duree = "Demie journée"

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
        fiche_brute = generer_fiche_revision(contenu, intitule, cursus, date, duree)
        fiche = valider_fiche(fiche_brute)

        nb_concepts = len(fiche.get("concepts_cles", []))
        nb_cas = len(fiche.get("cas_pratiques", []))
        etapes.append({
            "etape": "Fiche générée",
            "statut": "✅",
            "detail": f"{nb_concepts} concepts-clés, {nb_cas} cas pratique(s)"
        })

        # --- 5. Préparation du document final ---
        print("📄 Préparation du document final...")
        nom_fichier = construire_nom_fichier(cursus, intitule, date)
        
        # Chemins temporaires pour le traitement local
        BASE_DIR = Path(__file__).parent.parent
        chemin_modele_temp = temp_dir / "temp_modele.docx"
        chemin_final_temp = temp_dir / "temp_final.docx"

        # A. Téléchargement du modèle
        from drive_manager import MODELE_DOC_ID
        telecharger_modele(MODELE_DOC_ID, str(chemin_modele_temp))
        
        # B. Remplissage local
        remplir_docx_local(
            str(chemin_modele_temp),
            str(chemin_final_temp),
            fiche,
            intitule,
            date,
            cursus
        )

        # C. Upload et conversion
        try:
            doc_info = uploader_vers_drive_et_convertir(
                str(chemin_final_temp),
                nom_fichier
            )
        except Exception as upload_err:
            # Si erreur de quota, on tente un nettoyage d'urgence et on réessaie une fois
            if "quota" in str(upload_err).lower() or "403" in str(upload_err):
                print("⚠️ Quota dépassé détecté. Tentative de nettoyage d'urgence...")
                nettoyer_dossier_fiches(nb_jours_max=1) # Supprimer ce qui a plus de 24h
                vider_corbeille()
                # Réessai final
                doc_info = uploader_vers_drive_et_convertir(
                    str(chemin_final_temp),
                    nom_fichier
                )
            else:
                raise upload_err
        
        doc_id = doc_info["id"]
        etapes.append({
            "etape": "Google Doc créé",
            "statut": "✅",
            "detail": f"ID: {doc_id[:10]}..."
        })

        # Nettoyage des fichiers docx temporaires
        if chemin_modele_temp.exists(): chemin_modele_temp.unlink()
        if chemin_final_temp.exists(): chemin_final_temp.unlink()

        # Succès final
        etapes.append({
            "etape": "Finalisation",
            "statut": "✅",
            "detail": "Document rempli et prêt"
        })

        # --- Réponse finale ---
        # On adapte l'aperçu aux nouvelles clés du JSON
        apercu_fiche = {
            "objectifs": fiche.get("les_objectifs", [])[:4],
            "concepts": [s.get("titre") for s in fiche.get("sections_principales", [])[:3]],
            "points_essentiels": [fiche.get("l_essentiel", "")] if fiche.get("l_essentiel") else [],
            "a_des_cas_pratiques": fiche.get("cas_pratique", {}).get("afficher", False),
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
    # Diagnostic centralisé via drive_manager
    resultats = verifier_connexion()
    
    # Complément local
    gemini_ok = bool(os.getenv("GEMINI_API_KEY"))
    
    diagnostics = {
        "serveur": "✅ En ligne",
        "gemini_api": "✅ Configurée" if gemini_ok else "❌ GEMINI_API_KEY manquante",
        "google_drive": resultats.get("drive_connexion", "Inconnu"),
        "compte_utilisateur": resultats.get("compte_utilisateur", "Inconnu"),
        "dossier_cible": resultats.get("dossier_cible", "Inconnu"),
        "quota_usage": resultats.get("quota_usage", "Inconnu"),
        "modele_doc": resultats.get("modele_doc", "Inconnu"),
    }
    return jsonify(diagnostics)


@app.route("/api/clean", methods=["POST"])
def clean_drive():
    """Route manuelle pour vider l'espace du Service Account."""
    try:
        nb = nettoyer_dossier_fiches(nb_jours_max=0) # Supprime tout ce qui n'est pas d'aujourd'hui
        return jsonify({
            "succes": True, 
            "message": f"Nettoyage effectué. {nb} fichiers supprimés et corbeille vidée."
        })
    except Exception as e:
        return jsonify({"succes": False, "erreur": str(e)}), 500


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
