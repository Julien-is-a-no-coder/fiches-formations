"""
Module : setup_drive.py
Description : Script de configuration initiale — vérifie la connexion Google Drive/Docs
et affiche les instructions pour configurer le Service Account.

Usage : python execution/setup_drive.py
"""

import os
import sys
from pathlib import Path

# Ajouter le dossier execution au path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from drive_manager import verifier_connexion, FOLDER_FICHES, MODELE_DOC_ID, SERVICE_ACCOUNT_PATH


def afficher_instructions_service_account():
    """Affiche les instructions pour créer un Service Account Google."""
    email_sa = "[email du service account]"

    print("\n📋 INSTRUCTIONS — Configurer un Service Account Google :")
    print("=" * 60)
    print("\n1️⃣  Aller sur : https://console.cloud.google.com/iam-admin/serviceaccounts")
    print("2️⃣  Créer un projet ou sélectionner un existant")
    print("3️⃣  'Créer un compte de service' → nommer 'fiche-revision-bot'")
    print("4️⃣  'Créer et continuer' → 'Terminé'")
    print("5️⃣  Cliquer sur le compte de service créé → onglet 'Clés'")
    print("6️⃣  'Ajouter une clé' → 'Créer une clé' → JSON")
    print("7️⃣  Renommer le fichier téléchargé en 'service_account.json'")
    print("8️⃣  Placer 'service_account.json' à la racine du projet")
    print()
    print("9️⃣  Activer les APIs nécessaires :")
    print("    https://console.cloud.google.com/apis/library")
    print("    → Google Drive API (activer)")
    print("    → Google Docs API (activer)")
    print()
    print("🔟  Partager vos ressources Google Drive avec l'email du service account :")
    print(f"    Email : {email_sa}")
    print()
    print(f"    - Dossier cible (fiches) : https://drive.google.com/drive/folders/{FOLDER_FICHES}")
    print(f"      → Partager avec le SA en tant qu'Éditeur")
    print()
    print(f"    - Modèle Google Doc : https://docs.google.com/document/d/{MODELE_DOC_ID}")
    print(f"      → Partager avec le SA en tant qu'Éditeur")
    print()
    print("=" * 60)


def main():
    """Script de vérification principale."""
    print("\n🎓 Générateur de Fiches de Révision — Configuration")
    print("=" * 60)

    # Vérification des variables d'environnement
    gemini_key = os.getenv("GEMINI_API_KEY")
    print(f"\n🔑 GEMINI_API_KEY : {'✅ Configurée' if gemini_key else '❌ Manquante (ajouter dans .env)'}")

    # Vérification du Service Account
    sa_path = Path(SERVICE_ACCOUNT_PATH)
    sa_json_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")

    if sa_json_env:
        print("🔑 Service Account JSON : ✅ Via variable d'environnement (GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT)")
    elif sa_path.exists():
        print(f"🔑 Service Account JSON : ✅ Fichier trouvé ({SERVICE_ACCOUNT_PATH})")
    else:
        print(f"🔑 Service Account JSON : ❌ Fichier absent ({SERVICE_ACCOUNT_PATH})")
        afficher_instructions_service_account()
        return

    # Test de connexion Drive
    print("\n🔗 Test de connexion Google Drive...")
    resultats = verifier_connexion()

    for cle, valeur in resultats.items():
        labels = {
            "drive_connexion": "Drive API",
            "dossier_cible": "Dossier fiches",
            "modele_doc": "Modèle Google Doc",
        }
        label = labels.get(cle, cle)
        print(f"   {label} : {valeur}")

    # Résumé
    tous_ok = all("✅" in v for v in resultats.values())
    print()
    if tous_ok:
        print("✅ Tout est configuré ! Vous pouvez lancer l'application :")
        print("   python execution/app.py")
    else:
        print("⚠️  Des configurations sont requises. Corriger les erreurs ci-dessus.")
        if "❌" in resultats.get("modele_doc", ""):
            print()
            print("💡 RAPPEL : L'email du service account doit avoir accès au modèle Google Doc.")
            print("   → Ouvrir le modèle → Partager → Ajouter l'email du SA en tant qu'Éditeur")

    print()


if __name__ == "__main__":
    main()
