# 📚 Générateur de Fiches de Révision

## Objectif

Génère automatiquement une **fiche de révision/synthèse pédagogique** à partir d'un support de formation PDF.

L'IA (Gemini) analyse le PDF et crée une fiche structurée directement dans un **Google Doc** (copie du modèle), sauvegardée dans le dossier Google Drive cible avec le naming :
```
{Cursus}-{Intitulé de la séance}-{Date}
```

**Exemple :** `Bachelor RH-IA pour les RH-16-03-2026`

## Contenu de la fiche générée

- 📌 Objectifs de la séance
- 💡 Concepts-clés (terme + définition)
- 📝 Synthèse du contenu
- ✅ Points essentiels à retenir
- 📚 Ressources pédagogiques
- 🧪 Cas pratiques réalisés (si présents dans le PDF)
- ⚠️ Points de vigilance

## Prérequis

- Python 3.10+
- Clé API Google Gemini
- Fichier `service_account.json` (Google Service Account)
- Le service account doit avoir accès au dossier Drive cible et au modèle Google Doc

## Installation

```bash
# 1. Installer les dépendances Python
pip install -r requirements.txt

# 2. Configurer les variables d'environnement
copy .env.example .env
# Éditer .env avec tes clés API

# 3. Placer service_account.json à la racine

# 4. Tester la connexion Drive
python execution/setup_drive.py
```

## Usage

```bash
python execution/app.py
```

Ouvrir `http://localhost:5001` dans le navigateur.

## Structure du Projet

```
inner-zenith/
├── execution/
│   ├── app.py                 ← Serveur Flask (interface web)
│   ├── pdf_analyzer.py        ← Extraction et analyse PDF
│   ├── fiche_generator.py     ← Génération IA (Gemini)
│   ├── google_docs_builder.py ← Remplissage Google Doc via API
│   ├── drive_manager.py       ← Gestion Google Drive
│   └── setup_drive.py         ← Test de configuration initiale
├── templates/                 ← Interface utilisateur HTML/CSS/JS
├── sorties/                   ← Logs temporaires (non commités)
├── .env                       ← Clés API (ne jamais committer)
├── service_account.json       ← Service Google (ne jamais committer)
└── requirements.txt
```

## Google Drive — Configuration

- **Modèle Google Doc :** `1Ekwki-f3xkUNOyfxd0319GVi7f1g-go6`
- **Dossier cible :** `1t7JnOY1hO0cMwcCfqLc44eJJ_Mnz--LO`

## Déploiement Vercel

Pour déployer sur Vercel :
1. Pousser le code sur GitHub (en excluant les fichiers sensibles via `.gitignore`).
2. Créer un nouveau projet sur le Dashboard Vercel.
3. Ajouter les variables d'environnement suivantes :
   - `GEMINI_API_KEY` : Votre clé API.
   - `GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT` : Le contenu complet du fichier `service_account.json`.
   - `DRIVE_FOLDER_FICHES` : ID du dossier Drive.
   - `DRIVE_MODELE_DOC_ID` : ID du Doc modèle.
   - `VERCEL` : `1` (Détection auto activée).

L'application est configurée pour utiliser `api/index.py` comme point d'entrée serverless.

## Auteur

Julien Lesourd — Consultant Formateur IA & RH
