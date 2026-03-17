# 🚀 Walkthrough — Générateur de Fiches de Révision (V3 - Vercel Ready)

Ce document résume les fonctionnalités implémentées pour optimiser l'application, ajouter de nouvelles catégories et préparer le déploiement sur Vercel.

## ✨ Nouvelles Fonctionnalités & Améliorations

### 1. Compatibilité Vercel (Serverless)
L'application est désormais totalement compatible avec l'environnement serverless de Vercel :
- **Gestion des fichiers** : Les opérations d'écriture (PDF temporaires, génération DOCX) sont redirigées vers `/tmp`, car le système de fichiers racine de Vercel est en lecture seule.
- **Point d'entrée** : Création de `api/index.py` pour servir l'application Flask proprement.
- **Secrets** : Support de la variable `GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT` pour injecter les identifiants Google sans fichier physique sur le serveur.

### 2. Catégorie "Formation continue"
Une troisième option de cursus a été ajoutée :
- **Bachelor RH**
- **Mastère RH**
- **Formation continue** (Nouveau) : Cible les professionnels en reconversion ou montée en compétences.

### 3. Design Premium & UX Refined
- **Alignement** : Les cartes de sélection (Cursus et Durée) sont parfaitement alignées pour un rendu visuel symétrique.
- **Marges** : Réduction des marges dans le document généré (0.8 pouce) pour un aspect plus moderne et professionnel.
- **Libellés** : Simplification de "Conseil de l'expert" en **"Conseil"**.
- **Aération** : Ajout de sauts de ligne subtils sous les séparateurs de sections.

### 4. Robustesse des Liens
L'IA filtre désormais les liens hypertextes pour éviter d'insérer des URLs fictives. Seuls les liens réels détectés dans le PDF source ou les ressources standards validées sont conservés.

## 🚀 Déploiement

### 1. GitHub
Le projet a été poussé sur le dépôt : `Julien-is-a-no-coder/fiches-formations`.

### 2. Vercel
1.  Connectez votre dépôt GitHub à Vercel.
2.  Configurez les variables d'environnement suivantes dans le dashboard Vercel :
    - `GEMINI_API_KEY`
    - `GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT` (Copiez-collez le contenu de votre fichier JSON).
    - `DRIVE_FOLDER_FICHES` (ID du dossier cible).
    - `DRIVE_MODELE_DOC_ID` (ID de votre modèle).
3.  Déployez !

## 📁 Fichiers Clés

- `api/index.py` & `vercel.json` : Configuration pour le déploiement Vercel.
- `execution/app.py` : Logique de redirection vers `/tmp`.
- `execution/google_docs_builder.py` : Ajustement des marges et du design des titres.
- `templates/index.html` & `static/style.css` : Ajout de la nouvelle catégorie et fix d'alignement.
- `.env.example` : Modèle mis à jour pour les variables Vercel.

