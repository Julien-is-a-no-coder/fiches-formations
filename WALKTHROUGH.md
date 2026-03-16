# 🚀 Walkthrough — Générateur de Fiches de Révision (V2)

Ce document résume les fonctionnalités implémentées pour résoudre l'erreur de format Google Docs et intégrer la sélection de la durée des séances.

## ✨ Nouvelles Fonctionnalités

### 1. Compatibilité Totale avec les Modèles `.docx`
Plus besoin de convertir manuellement votre modèle Word en Google Doc natif. L'application gère désormais les deux formats :
- **Téléchargement** : Le modèle est récupéré depuis Google Drive (exporté en `.docx` si nécessaire).
- **Traitement Local** : Le remplissage des balises s'effectue localement avec la bibliothèque `python-docx`.
- **Conversion Auto** : Le fichier final est téléversé sur Drive avec une instruction de conversion, garantissant un **Google Doc natif** en sortie pour une édition facile.

### 2. Sélection de la Durée de Séance
Une nouvelle section a été ajoutée à l'interface pour choisir la durée :
- **Demie journée (3h30)** : Analyse standard.
- **Journée (7h00)** : Demande à l'IA une analyse plus profonde et génère un **déroulé pédagogique** détaillé.

### 3. Nouveau Placeholder `{{DEROULE}}`
Vous pouvez ajouter la balise `{{DEROULE}}` dans votre modèle Word/Google Doc. Elle sera remplacée par le planning suggéré par l'IA (uniquement pour les sessions d'une journée ou si l'IA identifie une structure temporelle).

## 🛠️ Configuration Requise

Assurez-vous que votre fichier `.env` contient l'ID du modèle (qu'il soit .docx ou Google Doc) :
```env
DRIVE_MODELE_DOC_ID=votre_id_ici
```

## 🧪 Comment Tester ?

1.  **Installer les nouvelles dépendances** :
    ```bash
    pip install -r requirements.txt
    ```
2.  **Lancer l'application** :
    ```bash
    python execution/app.py
    ```
3.  **Utiliser l'interface** :
    - Sélectionnez un cursus.
    - Choisissez **"Journée"** pour tester le nouveau module de déroulé.
    - Importez un PDF de formation.
    - Cliquez sur **"Générer la fiche"**.
4.  **Vérifier le résultat** :
    - Un lien vers le Google Doc apparaîtra à la fin.
    - Vérifiez que les textes et le déroulé (si applicable) sont bien insérés.

## 📁 Fichiers Modifiés

- `execution/app.py` : Nouveau workflow (Download -> local Edit -> Upload/Convert).
- `execution/drive_manager.py` : Fonctions de transfert et conversion Drive.
- `execution/google_docs_builder.py` : Passage à `python-docx` pour la manipulation des balises.
- `execution/fiche_generator.py` : Mise à jour du prompt Gemini pour inclure la durée et le déroulé.
- `templates/index.html` & `static/app.js` : Ajout des cartes de sélection de durée.
