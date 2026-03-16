"""
Module : drive_manager.py
Description : Gestion de l'authentification Google et des opérations sur Google Drive.
Utilise un Service Account JSON (compatible Vercel/serverless).
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

# Scopes nécessaires pour Drive et Docs
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

# Configuration via variables d'environnement
SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "./service_account.json")
FOLDER_FICHES = os.getenv("DRIVE_FOLDER_FICHES", "1t7JnOY1hO0cMwcCfqLc44eJJ_Mnz--LO")
MODELE_DOC_ID = os.getenv("DRIVE_MODELE_DOC_ID", "1Ekwki-f3xkUNOyfxd0319GVi7f1g-go6")


def _obtenir_credentials():
    """
    Obtient les credentials Google via Service Account JSON.
    Supporte à la fois un fichier local et une variable d'environnement JSON.

    Retourne:
        google.oauth2.service_account.Credentials

    Lève:
        FileNotFoundError: Si le fichier service_account.json est absent
        ValueError: Si la configuration est invalide
    """
    # Option 1 : Variable d'environnement contenant le JSON directement (pour Vercel)
    sa_json_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
    if sa_json_env:
        try:
            sa_info = json.loads(sa_json_env)
            return service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
        except json.JSONDecodeError as e:
            raise ValueError(f"Variable GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT invalide : {e}") from e

    # Option 2 : Fichier JSON local (développement)
    chemin = Path(SERVICE_ACCOUNT_PATH)
    if not chemin.exists():
        raise FileNotFoundError(
            f"Service Account JSON introuvable : {SERVICE_ACCOUNT_PATH}\n"
            "Créez un Service Account sur https://console.cloud.google.com/iam-admin/serviceaccounts\n"
            "Téléchargez la clé JSON et placez-la à la racine du projet."
        )
    return service_account.Credentials.from_service_account_file(str(chemin), scopes=SCOPES)


def obtenir_service_drive():
    """
    Crée et retourne un service Google Drive v3 authentifié.

    Retourne:
        Resource: Service Google Drive API v3
    """
    creds = _obtenir_credentials()
    return build("drive", "v3", credentials=creds)


def obtenir_service_docs():
    """
    Crée et retourne un service Google Docs v1 authentifié.

    Retourne:
        Resource: Service Google Docs API v1
    """
    creds = _obtenir_credentials()
    return build("docs", "v1", credentials=creds)


def copier_modele_vers_dossier(
    nom_fichier: str,
    dossier_id: str | None = None,
    modele_id: str | None = None
) -> dict:
    """
    Copie le Google Doc modèle dans le dossier cible et le renomme.

    Paramètres:
        nom_fichier (str): Nom du nouveau document (ex: "Bachelor RH-IA pour les RH-16-03-2026")
        dossier_id (str|None): ID du dossier Drive cible (défaut: FOLDER_FICHES)
        modele_id (str|None): ID du Google Doc modèle (défaut: MODELE_DOC_ID)

    Retourne:
        dict: {
            "id": str,          → ID du nouveau Google Doc
            "nom": str,         → Nom du fichier
            "lien_web": str,    → Lien d'édition Google Docs
            "lien_partage": str → Lien de partage direct
        }

    Lève:
        RuntimeError: Si la copie échoue
    """
    folder = dossier_id or FOLDER_FICHES
    modele = modele_id or MODELE_DOC_ID
    service = obtenir_service_drive()

    # Métadonnées pour la copie
    corps = {
        "name": nom_fichier,
        "parents": [folder],
    }

    try:
        fichier_copie = service.files().copy(
            fileId=modele,
            body=corps,
            fields="id,name,webViewLink"
        ).execute()

        file_id = fichier_copie.get("id")
        return {
            "id": file_id,
            "nom": fichier_copie.get("name"),
            "lien_web": fichier_copie.get("webViewLink"),
            "lien_partage": f"https://docs.google.com/document/d/{file_id}/edit",
        }
    except Exception as e:
        raise RuntimeError(
            f"Impossible de copier le modèle Google Doc ({modele}) : {e}"
        ) from e


def verifier_connexion() -> dict:
    """
    Vérifie que l'authentification Drive fonctionne et que les ressources sont accessibles.

    Retourne:
        dict: Résultats des vérifications
    """
    resultats = {}

    # Test connexion Drive
    try:
        service = obtenir_service_drive()
        # Vérifier accès au dossier cible
        service.files().get(fileId=FOLDER_FICHES, fields="id,name").execute()
        resultats["drive_connexion"] = "✅ Connecté"
        resultats["dossier_cible"] = f"✅ Accessible ({FOLDER_FICHES})"
    except FileNotFoundError as e:
        resultats["drive_connexion"] = f"❌ Service Account absent : {e}"
        return resultats
    except Exception as e:
        resultats["drive_connexion"] = f"❌ Erreur : {e}"
        resultats["dossier_cible"] = "⚠️ Non vérifié"

    # Test accès modèle Google Doc
    try:
        service = obtenir_service_drive()
        service.files().get(fileId=MODELE_DOC_ID, fields="id,name").execute()
        resultats["modele_doc"] = f"✅ Accessible ({MODELE_DOC_ID})"
    except Exception as e:
        resultats["modele_doc"] = f"❌ Erreur accès modèle : {e}"

    return resultats


if __name__ == "__main__":
    print("🔍 Vérification de la connexion Google Drive...")
    resultats = verifier_connexion()
    for cle, valeur in resultats.items():
        print(f"  {cle}: {valeur}")
