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
    date: str,
    duree: str = "Demie journée"
) -> dict:
    """
    Génère une fiche de révision complète à partir du contenu PDF de la formation.

    Paramètres:
        contenu_pdf (str): Texte complet extrait du support PDF
        intitule_seance (str): Intitulé de la séance de formation
        cursus (str): "Bachelor RH" ou "Mastère RH"
        date (str): Date de la séance (format YYYY-MM-DD ou DD/MM/YYYY)
        duree (str): "Demie journée" (3h30) ou "Journée" (7h00)

    Retourne:
        dict: {
            "objectifs_seance": list[str],
            "concepts_cles": list[dict(terme, definition)],
            "synthese_contenu": str,
            "points_essentiels": list[str],
            "ressources_pedagogiques": list[str],
            "cas_pratiques": list[dict(titre, description, consigne)],
            "points_vigilance": list[str],
            "deroule_pedagogique": str
        }
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
MISSION : Crée une fiche de révision complète et hautement qualitative pour la séance suivante.

INFORMATIONS DE LA SÉANCE :
- Intitulé : {intitule_seance}
- Cursus : {cursus}
- Date : {date}
- Durée prévue : {duree} (Note : Adapte la profondeur du contenu et du déroulé à cette durée)

SUPPORT DE FORMATION (contenu extrait du PDF) :
{contenu_tronque}

---

INSTRUCTIONS IMPÉRATIVES :
1. SYNTHÈSE PÉDAGOGIQUE & VARIATION : Ne fais pas qu'une simple liste de points (bullet points). Alterne les formats pour maintenir l'engagement : utilise des paragraphes narratifs pour expliquer des contextes, des listes pour les étapes, et des tableaux pour les comparaisons. Agis en vrai concepteur.
2. Structure ta réponse pour qu'elle ressemble à une vraie fiche de révision de Mastère RH (très synthétique, focus sur l'essentiel, orientée terrain et action).
3. Utilise la structure "sections_principales" pour découper le contenu en grands thèmes. Pour chaque thème, développe une explication courte (2-3 phrases) dans "chapeau_introductif" et varie les points clés.
4. Création de Tableaux : Dès que tu identifies une liste de caractéristiques, de profils avec des solutions, ou des concepts opposables, génère des données pour un "tableau_comparatif". C'est crucial pour la lisibilité !
5. Pour le cas pratique, sois précis : donne le contexte, les faits saillants, et les résultats ou livrables attendus (sous forme de listes courtes).
6. Points de vigilance & Ressources : Identifie les risques majeurs. Pour les ressources, n'extrais que les URLs et liens RÉELLEMENT présents dans le document source. NE GÉNÈRE AUCUN LIEN FICTIF. Si l'URL n'est pas écrite, ne l'invente pas. Formate-les en markdown [Nom du site/doc](URL).
7. INTERDICTION ABSOLUE D'UTILISER DES EMOJIS : Ce document est un support officiel. Ne génère AUCUN émoji.
8. CITATIONS : Si tu dois citer un texte ou une loi, utilise des guillemets simples (exemple : 'Loi du 24 octobre') ou des guillemets français (« »).
9. RESPECT DE LA LANGUE FRANÇAISE : N'utilise pas de majuscules inutiles. Seules les majuscules de début de phrase et de noms propres sont autorisées.
10. SOBRIÉTÉ : Évite les superlatifs et les phrases de remplissage. Chaque mot doit avoir une valeur pédagogique.

RÉPONDS UNIQUEMENT avec un JSON valide, sans markdown au format EXACT suivant :
{{
  "l_essentiel": "1 paragraphe très fort (max 4 phrases) résumant la vision globale ou la posture clé que l'apprenant doit retenir.",
  "les_objectifs": [ "La compétence visée 1", "La compétence visée 2" ],
  "sections_principales": [
    {{
      "titre": "1. Titre de la section (ex: Le Diagnostic RH)",
      "chapeau_introductif": "Phrase courte d'introduction du thème (optionnelle).",
      "points_cles": [
        "Traiter les faits : analyser la qualité, les délais plutôt que porter un jugement.",
        "Sécuriser : garantir la conformité à l'Art L1132-1."
      ],
      "tableau_comparatif": {{
        "afficher": true,
        "titre_tableau": "Comparatif des profils",
        "entetes": ["Profil", "Risques ou Obstacles", "Leviers et Solutions"],
        "lignes": [
          ["TDAH", "Interruptions fréquentes, perte de focus", "Méthodologie Pomodoro, isolation"],
          ["HPI", "Ennui rapide, besoin de sens", "Délégation de projets complexes"]
        ]
      }},
      "conseil_expert": "Privilégier toujours l'approche fonctionnelle plutôt que médicale pour éviter de stigmatiser."
    }}
  ],
  "cas_pratique": {{
    "afficher": true,
    "titre_atelier": "Atelier : Restitution Croisée",
    "organisation_livrables": ["Constituer des groupes de 3", "Produire une grille d'entretien"],
    "situations": [
      {{
        "nom_situation": "Cas A : Le collaborateur désengagé",
        "faits_et_attendus": "Faits : retards depuis 1 mois. Attendu : plan de relance motivation."
      }}
    ]
  }},
  "points_vigilance_et_ressources": [
    "Vigilance : ne jamais interroger sur des données de santé.",
    "Ressource : Guide du Défenseur des Droits."
  ]
}}
"""

    try:
        # Utilisation du modèle spécifié par l'utilisateur
        modele = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEME_EXPERT
        )
        
        reponse = modele.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2, # Température basse pour limiter les déviances JSON
                max_output_tokens=8192,
                response_mime_type="application/json",
            )
        )
        
        if not reponse or not reponse.text:
            raise RuntimeError("Gemini n'a renvoyé aucune réponse (texte vide).")

        texte = reponse.text.strip()

        # Nettoyage si jamais le modèle force des backticks malgré response_mime_type
        if texte.startswith("```json"):
            texte = texte[7:].strip()
        elif texte.startswith("```"):
            texte = texte[3:].strip()
        if texte.endswith("```"):
            texte = texte[:-3].strip()

        try:
            fiche = json.loads(texte)
            return fiche
        except json.JSONDecodeError as decode_error:
            # Si le JSON est tronqué, on tente une réparation basique ou on loggue la fin
            longueur = len(texte)
            fin = texte[-100:] if longueur > 100 else texte
            print(f"❌ Erreur JSON (Longueur: {longueur} chars). Fin de réponse : {fin}")
            
            # Message plus parlant pour l'utilisateur
            msg = f"Réponse Gemini tronquée ou malformée ({longueur} chars)."
            if "Unterminated string" in str(decode_error):
                msg += " Une chaîne de caractères n'a pas été fermée. Essayez un PDF plus court."
            
            raise RuntimeError(f"{msg} Détail: {decode_error}") from decode_error

    except Exception as e:
        if "google.api_core.exceptions.InvalidArgument" in str(e):
            raise RuntimeError(f"Modèle Gemini non trouvé ou invalide : {e}")
        raise RuntimeError(f"Erreur lors de la génération Gemini : {e}") from e


def valider_fiche(fiche: dict) -> dict:
    """
    Valide et normalise la structure de la nouvelle fiche générée.
    """
    defaults = {
        "l_essentiel": "Aucune information essentielle n'a été extraite.",
        "les_objectifs": [],
        "sections_principales": [],
        "cas_pratique": {
            "afficher": False, 
            "titre_atelier": "", 
            "organisation_livrables": [], 
            "situations": []
        },
        "points_vigilance_et_ressources": []
    }

    for cle, valeur_defaut in defaults.items():
        if cle not in fiche or fiche[cle] is None:
            fiche[cle] = valeur_defaut

    return fiche


if __name__ == "__main__":
    # Test de connexion Gemini
    if not GEMINI_API_KEY:
        print("[!] GEMINI_API_KEY manquante dans .env")
    else:
        print("[OK] API Gemini configuree")
        contenu_test = """Introduction a l'IA en RH. Seance 1 : Definitions et enjeux.
        L'intelligence artificielle est la simulation de processus d'intelligence humaine par des machines.
        Outils etudies : ChatGPT, Copilot, Claude. Cas pratique : Redaction d'une offre d'emploi avec ChatGPT."""
        try:
            fiche = generer_fiche_revision(contenu_test, "IA pour les RH - Seance 1", "Bachelor RH", "16/03/2026")
            print(json.dumps(fiche, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[ERROR] {e}")
