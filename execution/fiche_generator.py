"""
Module : fiche_generator.py
Description : Génération de la fiche de révision/synthèse via l'API Gemini.
Persona : expert en ingénierie pédagogique RH & IA.
Produit une fiche structurée et qualitative à partir du contenu PDF de la formation.
"""

import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configuration Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Prompt système : expert en ingénierie pédagogique
SYSTEME_EXPERT = """Tu es un expert en ingénierie pédagogique et en conception de formations professionnelles, \
spécialisé dans les domaines des Ressources Humaines et de l'Intelligence Artificielle.

Tu travailles pour des établissements d'enseignement supérieur (Bachelor RH, Mastère RH) et tu as \
plus de 15 ans d'expérience dans :
- La création de supports de révision synthétiques et mémorisables
- L'ingénierie de la formation professionnelle (AFEST, distanciel, blended learning)
- La pédagogie par compétences et l'approche programme
- La vulgarisation de concepts techniques pour des apprenants RH

Tes fiches de révision sont reconnues pour leur clarté, leur structure logique et leur exhaustivité. \
Tu t'assures que chaque fiche permet à un étudiant de réviser efficacement et de maîtriser les points clés \
de la séance sans avoir à relire le support complet.

Tu réponds TOUJOURS en français, de manière structurée et professionnelle."""


def generer_fiche_revision(
    contenu_pdf: str,
    intitule_seance: str,
    cursus: str,
    date: str
) -> dict:
    """
    Génère une fiche de révision complète à partir du contenu PDF de la formation.

    Paramètres:
        contenu_pdf (str): Texte complet extrait du support PDF
        intitule_seance (str): Intitulé de la séance de formation
        cursus (str): "Bachelor RH" ou "Mastère RH"
        date (str): Date de la séance (format YYYY-MM-DD ou DD/MM/YYYY)

    Retourne:
        dict: {
            "objectifs_seance": list[str],
            "concepts_cles": list[dict(terme, definition)],
            "synthese_contenu": str,
            "points_essentiels": list[str],
            "ressources_pedagogiques": list[str],
            "cas_pratiques": list[dict(titre, description, consigne)],
            "points_vigilance": list[str]
        }

    Lève:
        RuntimeError: Si la génération Gemini échoue
        ValueError: Si la clé API n'est pas configurée
    """
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY manquante dans .env. "
            "Obtenir une clé sur https://aistudio.google.com/app/apikey"
        )

    # Limiter le contenu pour respecter les limites de tokens (12 000 chars max)
    contenu_tronque = contenu_pdf[:12000]
    if len(contenu_pdf) > 12000:
        contenu_tronque += "\n\n[... contenu tronqué pour l'analyse ...]"

    prompt = f"""
{SYSTEME_EXPERT}

---

MISSION : Crée une fiche de révision complète et hautement qualitative pour la séance suivante.

INFORMATIONS DE LA SÉANCE :
- Intitulé : {intitule_seance}
- Cursus : {cursus}
- Date : {date}

SUPPORT DE FORMATION (contenu extrait du PDF) :
{contenu_tronque}

---

INSTRUCTIONS IMPÉRATIVES :
1. Analyse attentivement tout le contenu du support pour identifier les enseignements clés.
2. Développe chaque section de manière substantielle — évite les formulations vagues ou génériques.
3. Les concepts-clés doivent être précis, définis avec une formulation claire et mémorisable.
4. La synthèse doit être rédigée en paragraphes fluides (pas de liste à puces), couvrant l'essentiel de la séance.
5. Les points essentiels doivent être formulés comme des affirmations claires et mémorisables (max 15 mots chacun).
6. Pour les ressources pédagogiques : cite uniquement celles mentionnées dans le support (outils, articles, livres, sites) — sinon laisse vide.
7. Pour les cas pratiques : décris uniquement les exercices/mises en situation effectivement présents dans le PDF — sinon laisse la liste vide.
8. Les points de vigilance = erreurs courantes ou points de confusion à anticiper pour les étudiants.

RÉPONDS UNIQUEMENT avec un JSON valide, sans markdown, sans explication, au format EXACT suivant :
{{
  "objectifs_seance": [
    "Objectif pédagogique 1 (verbe d'action + compétence visée)",
    "Objectif pédagogique 2",
    "Objectif pédagogique 3"
  ],
  "concepts_cles": [
    {{
      "terme": "Nom du concept",
      "definition": "Définition claire et précise en 1-2 phrases"
    }}
  ],
  "synthese_contenu": "Synthèse rédigée en 3-5 paragraphes couvrant l'ensemble du contenu abordé pendant la séance...",
  "points_essentiels": [
    "Point essentiel 1 : affirmation mémorisable",
    "Point essentiel 2",
    "Point essentiel 3"
  ],
  "ressources_pedagogiques": [
    "Ressource 1 (outil / article / livre mentionné dans le support)",
    "Ressource 2"
  ],
  "cas_pratiques": [
    {{
      "titre": "Nom du cas pratique",
      "description": "Description du contexte et des objectifs de l'exercice",
      "consigne": "Instructions données aux participants"
    }}
  ],
  "points_vigilance": [
    "Point de vigilance 1 : erreur ou confusion fréquente à éviter",
    "Point de vigilance 2"
  ]
}}
"""

    try:
        modele = genai.GenerativeModel("models/gemini-2.5-flash")
        reponse = modele.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,
            )
        )
        texte = reponse.text.strip()

        # Nettoyage du JSON (suppression des balises markdown si présentes)
        texte = re.sub(r"^```json\s*", "", texte)
        texte = re.sub(r"```\s*$", "", texte)
        texte = texte.strip()

        fiche = json.loads(texte)
        return fiche

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"La réponse Gemini n'est pas un JSON valide : {e}\n"
            f"Réponse reçue : {texte[:500]}"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la génération Gemini : {e}") from e


def valider_fiche(fiche: dict) -> dict:
    """
    Valide et normalise la structure de la fiche générée.
    Garantit que toutes les clés attendues sont présentes.

    Paramètres:
        fiche (dict): Fiche brute retournée par Gemini

    Retourne:
        dict: Fiche normalisée avec valeurs par défaut si nécessaire
    """
    defaults = {
        "objectifs_seance": [],
        "concepts_cles": [],
        "synthese_contenu": "",
        "points_essentiels": [],
        "ressources_pedagogiques": [],
        "cas_pratiques": [],
        "points_vigilance": [],
    }

    for cle, valeur_defaut in defaults.items():
        if cle not in fiche or fiche[cle] is None:
            fiche[cle] = valeur_defaut

    return fiche


if __name__ == "__main__":
    # Test de connexion Gemini
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY manquante dans .env")
    else:
        print("✅ API Gemini configurée")
        contenu_test = """Introduction à l'IA en RH. Séance 1 : Définitions et enjeux.
        L'intelligence artificielle est la simulation de processus d'intelligence humaine par des machines.
        Outils étudiés : ChatGPT, Copilot, Claude. Cas pratique : Rédaction d'une offre d'emploi avec ChatGPT."""
        fiche = generer_fiche_revision(contenu_test, "IA pour les RH - Séance 1", "Bachelor RH", "16/03/2026")
        print(json.dumps(fiche, ensure_ascii=False, indent=2))
