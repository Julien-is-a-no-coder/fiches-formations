"""
Module : drive_manager.py
Description : Gestion de l'authentification Google et des opérations sur Google Drive/Docs.
Utilise OAuth2 en local (credentials.json + token.pickle)
et Service Account en production Vercel (GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT).
"""

import os
import json
import pickle
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Scopes nécessaires pour Drive et Docs
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

# Chemins de configuration
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "./token.pickle")

# Configuration Drive
FOLDER_FICHES = os.getenv("DRIVE_FOLDER_FICHES", "1t7JnOY1hO0cMwcCfqLc44eJJ_Mnz--LO")
MODELE_DOC_ID = os.getenv("DRIVE_MODELE_DOC_ID", "1Ekwki-f3xkUNOyfxd0319GVi7f1g-go6")


def _obtenir_credentials():
    """
    Obtient les credentials Google.
    Priorité :
      1. Service Account JSON (variable d'env — production Vercel)
      2. OAuth2 token.pickle + credentials.json (développement local)

    Retourne:
        google credentials

    Lève:
        FileNotFoundError: Si aucune configuration n'est trouvée
    """
    # --- Option 1 : Service Account (Vercel) ---
    sa_json_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
    if sa_json_env:
        from google.oauth2 import service_account
        sa_info = json.loads(sa_json_env)
        return service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)

    sa_fichier = Path(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "./service_account.json"))
    if sa_fichier.exists():
        from google.oauth2 import service_account
        return service_account.Credentials.from_service_account_file(str(sa_fichier), scopes=SCOPES)

    # --- Option 2 : OAuth2 local (credentials.json + token.pickle) ---
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None

    # Charger le token sauvegardé
    token = Path(TOKEN_PATH)
    if token.exists():
        with open(str(token), "rb") as f:
            creds = pickle.load(f)

    # Rafraîchir ou re-authentifier si nécessaire
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = Path(CREDENTIALS_PATH)
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"Aucune configuration Google trouvée.\n"
                    f"Attendu : credentials.json à '{CREDENTIALS_PATH}'\n"
                    "Consultez le README pour configurer l'accès Google."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Sauvegarder le token
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    return creds


def obtenir_service_drive():
    """
    Crée et retourne un service Google Drive v3 authentifié.

    Retourne:
        Resource: Service Google Drive API v3
    """
    from googleapiclient.discovery import build
    creds = _obtenir_credentials()
    return build("drive", "v3", credentials=creds)


def obtenir_service_docs():
    """
    Crée et retourne un service Google Docs v1 authentifié.

    Retourne:
        Resource: Service Google Docs API v1
    """
    from googleapiclient.discovery import build
    creds = _obtenir_credentials()
    return build("docs", "v1", credentials=creds)


def copier_modele_vers_dossier(
    nom_fichier: str,
    dossier_id: str | None = None,
    modele_id: str | None = None
) -> dict:
    """
    OBSOLÈTE : Cette fonction copiait directement sur Drive. 
    Préférer telecharger_modele + modification locale + uploader_vers_drive_et_convertir.
    """
    folder = dossier_id or FOLDER_FICHES
    modele = modele_id or MODELE_DOC_ID
    service = obtenir_service_drive()

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


def telecharger_modele(file_id: str, chemin_destination: str) -> str:
    """
    Télécharge un fichier modèle depuis Google Drive.
    Si c'est un Google Doc, l'exporte en .docx.
    """
    from googleapiclient.http import MediaIoBaseDownload
    import io
    service = obtenir_service_drive()

    path = Path(chemin_destination)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Essayer d'abord le téléchargement direct (si c'est déjà un .docx)
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    except Exception as e:
        # Si échec, c'est probablement un Google Doc natif -> export
        request = service.files().export_media(
            fileId=file_id,
            mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

    with open(str(path), "wb") as f:
        f.write(fh.getvalue())
    return str(path)


def uploader_vers_drive_et_convertir(
    chemin_local: str,
    nom_destination: str,
    dossier_id: str | None = None
) -> dict:
    """
    Upload un .docx local vers Drive et le convertit en Google Doc natif.
    """
    from googleapiclient.http import MediaFileUpload
    folder = dossier_id or FOLDER_FICHES
    service = obtenir_service_drive()

    metadata = {
        "name": nom_destination,
        "parents": [folder],
        "mimeType": "application/vnd.google-apps.document"  # Force la conversion
    }

    media = MediaFileUpload(
        chemin_local,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        resumable=False
    )

    fichier = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,name,webViewLink"
    ).execute()

    file_id = fichier.get("id")
    return {
        "id": file_id,
        "nom": fichier.get("name"),
        "lien_web": fichier.get("webViewLink"),
        "lien_partage": f"https://docs.google.com/document/d/{file_id}/edit",
    }


def vider_corbeille() -> bool:
    """
    Vide définitivement la corbeille du compte (Service Account).
    Essentiel pour libérer de l'espace sur un compte saturé.
    """
    try:
        service = obtenir_service_drive()
        service.files().emptyTrash().execute()
        return True
    except Exception as e:
        print(f"[ERROR] Impossible de vider la corbeille : {e}")
        return False


def nettoyer_dossier_fiches(nb_jours_max: int = 2) -> int:
    """
    Supprime les fichiers du dossier fiches ayant plus de X jours.
    Ceci libère le quota du Service Account.
    """
    from datetime import datetime, timedelta, timezone
    
    service = obtenir_service_drive()
    folder = FOLDER_FICHES
    
    # Calculer la date limite (si nb_jours_max=0, on prend l'instant t)
    # On ajoute une petite marge pour éviter de supprimer le fichier en cours
    date_limite = datetime.now(timezone.utc) - timedelta(days=nb_jours_max)
    if nb_jours_max == 0:
        # Si on veut TOUT supprimer, on prend ce qui a plus de 1 minute
        date_limite = datetime.now(timezone.utc) - timedelta(minutes=1)
    
    date_limite_str = date_limite.isoformat().replace("+00:00", "Z")

    try:
        # Lister les fichiers dans le dossier
        query = f"'{folder}' in parents and trashed = false and createdTime < '{date_limite_str}'"
        nb_supprimes = 0
        
        # Pagination pour tout supprimer
        page_token = None
        while True:
            resultats = service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, createdTime)",
                pageSize=100,
                pageToken=page_token
            ).execute()

            fichiers = resultats.get("files", [])
            for f in fichiers:
                service.files().delete(fileId=f["id"]).execute()
                nb_supprimes += 1
            
            page_token = resultats.get("nextPageToken")
            if not page_token:
                break
            
        # Toujours vider la corbeille si on a supprimé
        vider_corbeille()
            
        return nb_supprimes
    except Exception as e:
        print(f"[ERROR] Erreur lors du nettoyage : {e}")
        return 0


def obtenir_quota_usage() -> tuple[str, str]:
    """Récupère l'état du quota et l'email du compte."""
    try:
        service = obtenir_service_drive()
        about = service.about().get(fields="user, storageQuota").execute()
        user = about.get("user", {}).get("emailAddress", "Inconnu")
        quota = about.get("storageQuota", {})
        limit = int(quota.get("limit", 0))
        usage = int(quota.get("usage", 0))
        
        info = ""
        if limit > 0:
            pourcentage = (usage / limit) * 100
            info = f"{usage / (1024**2):.1f}MB / {limit / (1024**2):.1f}MB ({pourcentage:.1f}%)"
        else:
            info = f"{usage / (1024**2):.1f}MB / Illimité"
        
        return user, info
    except Exception as e:
        return "Erreur", f"Erreur quota : {e}"


def verifier_connexion() -> dict:
    """
    Vérifie que l'authentification Drive fonctionne et que les ressources sont accessibles.

    Retourne:
        dict: Résultats des vérifications
    """
    resultats = {}

    try:
        service = obtenir_service_drive()
        # Vérifier accès au dossier cible
        dossier = service.files().get(fileId=FOLDER_FICHES, fields="id,name").execute()
        resultats["drive_connexion"] = "✅ Connecté"
        resultats["dossier_cible"] = f"✅ Accessible ({dossier.get('name', FOLDER_FICHES)})"
        
        email, quota = obtenir_quota_usage()
        resultats["compte_utilisateur"] = email
        resultats["quota_usage"] = quota
    except FileNotFoundError as e:
        resultats["drive_connexion"] = f"❌ Config absente : {e}"
        return resultats
    except Exception as e:
        resultats["drive_connexion"] = f"❌ Erreur : {e}"
        resultats["dossier_cible"] = "⚠️ Non vérifié"
        resultats["quota_usage"] = "⚠️ Non vérifié"
        resultats["compte_utilisateur"] = "⚠️ Non vérifié"

    # Test accès modèle Google Doc
    try:
        service = obtenir_service_drive()
        doc = service.files().get(fileId=MODELE_DOC_ID, fields="id,name,mimeType").execute()
        resultats["modele_doc"] = f"✅ Accessible ({doc.get('name', MODELE_DOC_ID)})"
    except Exception as e:
        resultats["modele_doc"] = f"❌ Erreur accès modèle : {e}"

    return resultats


if __name__ == "__main__":
    print("🔍 Vérification de la connexion Google Drive...")
    resultats = verifier_connexion()
    for cle, valeur in resultats.items():
        print(f"  {cle}: {valeur}")
