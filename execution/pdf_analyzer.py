"""
Module : pdf_analyzer.py
Description : Extraction et analyse du contenu d'un support de formation PDF.
Détecte automatiquement les sections, les titres et construit un index du contenu.
"""

import re
from pathlib import Path

import pdfplumber
from pypdf import PdfReader


def extraire_texte_pdf(chemin_pdf: str) -> dict:
    """
    Extrait et structure le contenu textuel d'un fichier PDF.

    Paramètres:
        chemin_pdf (str): Chemin absolu vers le fichier PDF

    Retourne:
        dict: {
            "contenu_complet": str,      → Tout le texte extrait
            "nb_pages": int,             → Nombre de pages
            "sections": list[str],       → Titres de sections détectés
            "metadonnees": dict          → Métadonnées du PDF si disponibles
        }

    Lève:
        FileNotFoundError: Si le fichier est introuvable
        ValueError: Si le fichier n'est pas un PDF valide
    """
    chemin = Path(chemin_pdf)
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier PDF introuvable : {chemin_pdf}")

    if chemin.suffix.lower() != ".pdf":
        raise ValueError(f"Le fichier doit être un PDF : {chemin_pdf}")

    # --- Extraction du texte avec pdfplumber (meilleur pour les tableaux) ---
    pages_texte = []
    with pdfplumber.open(str(chemin)) as pdf:
        nb_pages = len(pdf.pages)
        for page in pdf.pages:
            texte_page = page.extract_text()
            if texte_page:
                pages_texte.append(texte_page.strip())

    # Fallback vers pypdf si pdfplumber échoue (PDFs scannés ou protégés)
    if not pages_texte:
        reader = PdfReader(str(chemin))
        nb_pages = len(reader.pages)
        for page in reader.pages:
            texte = page.extract_text()
            if texte:
                pages_texte.append(texte.strip())

    contenu_complet = "\n\n".join(pages_texte)

    # --- Détection des sections / titres ---
    sections = _detecter_sections(contenu_complet)

    # --- Métadonnées du PDF ---
    metadonnees = {}
    try:
        reader = PdfReader(str(chemin))
        info = reader.metadata
        if info:
            metadonnees = {
                "titre": getattr(info, "title", "") or "",
                "auteur": getattr(info, "author", "") or "",
                "sujet": getattr(info, "subject", "") or "",
            }
    except Exception:
        pass

    return {
        "contenu_complet": contenu_complet,
        "nb_pages": nb_pages,
        "sections": sections,
        "metadonnees": metadonnees,
    }


def _detecter_sections(texte: str) -> list[str]:
    """
    Détecte les titres/sections dans le texte extrait du PDF.

    Paramètres:
        texte (str): Texte brut extrait du PDF

    Retourne:
        list[str]: Liste des titres de sections détectés
    """
    sections = []
    lignes = texte.split("\n")

    for ligne in lignes:
        ligne_clean = ligne.strip()
        if not ligne_clean:
            continue

        # Heuristiques de détection de titre :
        # - Ligne courte (< 80 caractères)
        # - Commence par un numéro (1., 2., I., A., etc.)
        # - En majuscules ou Première Lettre Majuscule
        # - Pas une phrase complète (pas de point final)
        est_titre = False

        if len(ligne_clean) < 80 and not ligne_clean.endswith((".", ",", ";")):
            # Titre numéroté
            if re.match(r"^(\d+[\.\)]\s|[IVX]+[\.\)]\s|[A-Z][\.\)]\s)", ligne_clean):
                est_titre = True
            # Tout en majuscules
            elif ligne_clean.isupper() and len(ligne_clean) > 3:
                est_titre = True
            # Commence par une majuscule et contient peu de mots (titre probable)
            elif ligne_clean[0].isupper() and len(ligne_clean.split()) <= 8:
                est_titre = True

        if est_titre and ligne_clean not in sections:
            sections.append(ligne_clean)

    # Limiter à 30 sections maximum pour éviter les faux positifs
    return sections[:30]


if __name__ == "__main__":
    # Test rapide en ligne de commande
    import sys
    if len(sys.argv) > 1:
        resultat = extraire_texte_pdf(sys.argv[1])
        print(f"✅ {resultat['nb_pages']} pages extraites")
        print(f"📋 {len(resultat['sections'])} sections détectées")
        print(f"📝 {len(resultat['contenu_complet'])} caractères")
        print("\nSections détectées :")
        for s in resultat["sections"][:10]:
            print(f"  — {s}")
    else:
        print("Usage : python pdf_analyzer.py <chemin_du_pdf>")
