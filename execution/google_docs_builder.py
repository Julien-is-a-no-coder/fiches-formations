"""
Module : google_docs_builder.py
Description : Remplissage du Google Doc copié via l'API Google Docs v1.
Remplace les placeholders dans le document modèle avec le contenu de la fiche générée.

Placeholders attendus dans le modèle Google Doc :
  {{DATE}}            → Date de la séance
  {{INTITULÉ}}        → Intitulé de la séance
  {{CURSUS}}          → Bachelor RH / Mastère RH
  {{OBJECTIFS}}       → Liste des objectifs de la séance
  {{CONCEPTS}}        → Tableau des concepts-clés
  {{SYNTHESE}}        → Synthèse rédigée du contenu
  {{POINTS_ESSENTIELS}} → Liste des points essentiels
  {{RESSOURCES}}      → Liste des ressources pédagogiques
  {{CAS_PRATIQUES}}   → Description des cas pratiques
  {{POINTS_VIGILANCE}} → Points de vigilance
"""

from drive_manager import obtenir_service_docs


def formater_date(date_str: str) -> str:
    """
    Formate une date en français lisible.

    Paramètres:
        date_str (str): Date au format YYYY-MM-DD ou DD/MM/YYYY

    Retourne:
        str: Date formatée (ex: "16 mars 2026")
    """
    mois = {
        "01": "janvier", "02": "février", "03": "mars", "04": "avril",
        "05": "mai", "06": "juin", "07": "juillet", "08": "août",
        "09": "septembre", "10": "octobre", "11": "novembre", "12": "décembre",
    }

    if "-" in date_str and len(date_str) == 10:
        # Format YYYY-MM-DD
        parties = date_str.split("-")
        annee, mois_num, jour = parties[0], parties[1], parties[2]
    elif "/" in date_str:
        # Format DD/MM/YYYY
        parties = date_str.split("/")
        jour, mois_num, annee = parties[0], parties[1], parties[2]
    else:
        return date_str

    return f"{int(jour)} {mois.get(mois_num, mois_num)} {annee}"


def construire_texte_objectifs(objectifs: list[str]) -> str:
    """Formate la liste des objectifs en texte structuré."""
    if not objectifs:
        return "— Objectifs non renseignés"
    return "\n".join(f"• {obj}" for obj in objectifs)


def construire_texte_concepts(concepts: list[dict]) -> str:
    """Formate les concepts-clés en texte (terme + définition)."""
    if not concepts:
        return "— Concepts non renseignés"
    lignes = []
    for c in concepts:
        terme = c.get("terme", "")
        definition = c.get("definition", "")
        lignes.append(f"▸ {terme}\n{definition}")
    return "\n\n".join(lignes)


def construire_texte_points(points: list[str], prefixe: str = "✓") -> str:
    """Formate une liste de points en texte structuré."""
    if not points:
        return "— Non renseigné"
    return "\n".join(f"{prefixe} {p}" for p in points)


def construire_texte_ressources(ressources: list[str]) -> str:
    """Formate la liste des ressources pédagogiques."""
    if not ressources:
        return "— Aucune ressource spécifique mentionnée dans le support"
    return "\n".join(f"📚 {r}" for r in ressources)


def construire_texte_cas_pratiques(cas_pratiques: list[dict]) -> str:
    """Formate les cas pratiques en texte structuré."""
    if not cas_pratiques:
        return "— Aucun cas pratique identifié dans le support de formation"
    blocs = []
    for i, cas in enumerate(cas_pratiques, 1):
        titre = cas.get("titre", f"Cas pratique {i}")
        description = cas.get("description", "")
        consigne = cas.get("consigne", "")
        bloc = f"🧪 Cas pratique {i} : {titre}"
        if description:
            bloc += f"\n{description}"
        if consigne:
            bloc += f"\nConsigne : {consigne}"
        blocs.append(bloc)
    return "\n\n".join(blocs)


def remplir_google_doc(
    doc_id: str,
    fiche: dict,
    intitule: str,
    date: str,
    cursus: str
) -> bool:
    """
    Remplace les placeholders dans le Google Doc avec le contenu de la fiche.

    Paramètres:
        doc_id (str): ID du Google Doc à modifier (déjà copié)
        fiche (dict): Données de la fiche générée par fiche_generator
        intitule (str): Intitulé de la séance
        date (str): Date de la séance
        cursus (str): Cursus (Bachelor RH / Mastère RH)

    Retourne:
        bool: True si le remplissage a réussi

    Lève:
        RuntimeError: Si l'API Google Docs retourne une erreur
    """
    service = obtenir_service_docs()
    date_formatee = formater_date(date)

    # Construction de la map des remplacements
    remplacements = {
        "{{DATE}}": date_formatee,
        "{{INTITULÉ}}": intitule,
        "{{CURSUS}}": cursus,
        "{{OBJECTIFS}}": construire_texte_objectifs(fiche.get("objectifs_seance", [])),
        "{{CONCEPTS}}": construire_texte_concepts(fiche.get("concepts_cles", [])),
        "{{SYNTHESE}}": fiche.get("synthese_contenu", ""),
        "{{POINTS_ESSENTIELS}}": construire_texte_points(fiche.get("points_essentiels", []), "✓"),
        "{{RESSOURCES}}": construire_texte_ressources(fiche.get("ressources_pedagogiques", [])),
        "{{CAS_PRATIQUES}}": construire_texte_cas_pratiques(fiche.get("cas_pratiques", [])),
        "{{POINTS_VIGILANCE}}": construire_texte_points(fiche.get("points_vigilance", []), "⚠️"),
    }

    # Construction des requêtes batchUpdate
    requests = []
    for placeholder, valeur in remplacements.items():
        if not valeur:
            valeur = "—"
        requests.append({
            "replaceAllText": {
                "containsText": {
                    "text": placeholder,
                    "matchCase": True,
                },
                "replaceText": valeur,
            }
        })

    if not requests:
        return True

    try:
        service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests}
        ).execute()
        return True
    except Exception as e:
        raise RuntimeError(
            f"Erreur lors du remplissage du Google Doc ({doc_id}) : {e}"
        ) from e


def construire_nom_fichier(cursus: str, intitule: str, date: str) -> str:
    """
    Construit le nom du fichier selon la convention de nommage.

    Format : "{Cursus}-{Intitulé}-{Date (DD-MM-YYYY)}"
    Exemple : "Bachelor RH-IA pour les RH-16-03-2026"

    Paramètres:
        cursus (str): Cursus de la formation
        intitule (str): Intitulé de la séance
        date (str): Date au format YYYY-MM-DD ou DD/MM/YYYY

    Retourne:
        str: Nom du fichier formaté
    """
    # Normaliser la date en DD-MM-YYYY
    if "-" in date and len(date) == 10:
        parties = date.split("-")
        date_nom = f"{parties[2]}-{parties[1]}-{parties[0]}"
    elif "/" in date:
        date_nom = date.replace("/", "-")
    else:
        date_nom = date

    # Nettoyer l'intitulé (supprimer les caractères spéciaux pour le nom de fichier)
    intitule_net = intitule.replace("/", "-").replace("\\", "-").strip()

    return f"{cursus}-{intitule_net}-{date_nom}"
