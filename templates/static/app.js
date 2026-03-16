/**
 * app.js — Logique frontend du Générateur de Fiches de Révision
 * Gestion du formulaire, de l'upload PDF, de la progression et de l'affichage des résultats.
 */

// ─────────────────────────────────────────────
// Initialisation
// ─────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  initialiserDate();
  initialiserUpload();
  initialiserFormulaire();
  initialiserCursusCards();
  initialiserDureeCards();
  verifierStatut();
});


/** Définit la date du jour par défaut dans le champ date */
function initialiserDate() {
  const champDate = document.getElementById("date");
  if (champDate && !champDate.value) {
    const aujourd_hui = new Date().toISOString().split("T")[0];
    champDate.value = aujourd_hui;
  }
}


/** Gestion des cards de sélection de cursus */
function initialiserCursusCards() {
  const radioButtons = document.querySelectorAll('input[name="cursus"]');

  function mettreAJourCards() {
    radioButtons.forEach(radio => {
      const card = radio.closest(".cursus-card");
      if (radio.checked) {
        card.classList.add("selected");
      } else {
        card.classList.remove("selected");
      }
    });
  }

  radioButtons.forEach(radio => {
    radio.addEventListener("change", mettreAJourCards);
  });

  mettreAJourCards(); // État initial
}


/** Gestion des cards de sélection de durée */
function initialiserDureeCards() {
  const radioButtons = document.querySelectorAll('input[name="duree"]');

  function mettreAJourCards() {
    radioButtons.forEach(radio => {
      const card = radio.closest(".cursus-card");
      if (radio.checked) {
        card.classList.add("selected");
      } else {
        card.classList.remove("selected");
      }
    });
  }

  radioButtons.forEach(radio => {
    radio.addEventListener("change", mettreAJourCards);
  });

  mettreAJourCards(); // État initial
}


// ─────────────────────────────────────────────
// Upload PDF
// ─────────────────────────────────────────────

function initialiserUpload() {
  const uploadZone = document.getElementById("upload-zone");
  const inputFichier = document.getElementById("pdf");
  const placeholder = document.getElementById("upload-placeholder");
  const preview = document.getElementById("upload-preview");
  const nomFichier = document.getElementById("file-name-display");
  const tailleFichier = document.getElementById("file-size-display");
  const btnSupprimer = document.getElementById("file-remove");

  // Clic sur la zone
  uploadZone.addEventListener("click", (e) => {
    if (e.target !== btnSupprimer && !btnSupprimer.contains(e.target)) {
      inputFichier.click();
    }
  });

  // Sélection de fichier
  inputFichier.addEventListener("change", () => {
    if (inputFichier.files.length > 0) {
      afficherFichier(inputFichier.files[0]);
    }
  });

  // Drag & Drop
  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.classList.add("drag-over");
  });
  uploadZone.addEventListener("dragleave", () => {
    uploadZone.classList.remove("drag-over");
  });
  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("drag-over");
    const fichiers = e.dataTransfer.files;
    if (fichiers.length > 0 && fichiers[0].type === "application/pdf") {
      // Simuler la sélection dans l'input
      const dt = new DataTransfer();
      dt.items.add(fichiers[0]);
      inputFichier.files = dt.files;
      afficherFichier(fichiers[0]);
    }
  });

  // Supprimer le fichier sélectionné
  btnSupprimer.addEventListener("click", (e) => {
    e.stopPropagation();
    inputFichier.value = "";
    placeholder.classList.remove("hidden");
    preview.classList.add("hidden");
    uploadZone.classList.remove("has-file");
  });

  /** Affiche le nom et la taille du fichier sélectionné */
  function afficherFichier(fichier) {
    nomFichier.textContent = fichier.name;
    tailleFichier.textContent = formaterTaille(fichier.size);
    placeholder.classList.add("hidden");
    preview.classList.remove("hidden");
    uploadZone.classList.add("has-file");
  }
}

/** Formate une taille en octets en string lisible (Ko / Mo) */
function formaterTaille(octets) {
  if (octets < 1024 * 1024) return `${Math.round(octets / 1024)} Ko`;
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`;
}


// ─────────────────────────────────────────────
// Formulaire & Génération
// ─────────────────────────────────────────────

function initialiserFormulaire() {
  const form = document.getElementById("form-generation");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await lancerGeneration(form);
  });
}


async function lancerGeneration(form) {
  const btnGenerer = document.getElementById("btn-generate");
  const resultsZone = document.getElementById("results-zone");

  // Validation côté client
  const intitule = document.getElementById("intitule").value.trim();
  const date = document.getElementById("date").value.trim();
  const pdfInput = document.getElementById("pdf");

  if (!intitule) { afficherErreurChamp("intitule", "L'intitulé est requis."); return; }
  if (!date) { afficherErreurChamp("date", "La date est requise."); return; }
  if (!pdfInput.files || pdfInput.files.length === 0) {
    alert("Veuillez sélectionner un fichier PDF.");
    return;
  }

  // Préparer l'UI de chargement
  btnGenerer.disabled = true;
  btnGenerer.innerHTML = '<span class="spinner"></span><span class="btn-text">Génération en cours...</span>';

  resultsZone.classList.remove("hidden");
  document.getElementById("results-card").classList.add("hidden");
  document.getElementById("error-card").classList.add("hidden");
  nettoyer("steps-list");

  // Construire le FormData
  const formData = new FormData(form);

  try {
    const reponse = await fetch("/api/generer", {
      method: "POST",
      body: formData,
    });

    // Affichage progressif des étapes (si dispo dans le header)
    const donnees = await reponse.json();

    // Afficher les étapes de progression
    if (donnees.etapes) {
      donnees.etapes.forEach((etape, i) => {
        setTimeout(() => afficherEtape(etape), i * 180);
      });
    }

    if (donnees.succes) {
      // Afficher les résultats après les étapes
      const delai = (donnees.etapes?.length || 0) * 180 + 400;
      setTimeout(() => afficherResultats(donnees), delai);
    } else {
      const delai = (donnees.etapes?.length || 0) * 180 + 200;
      setTimeout(() => afficherErreur(donnees.erreur, donnees.trace), delai);
    }

  } catch (err) {
    afficherEtape({ etape: "Erreur réseau", statut: "❌", detail: err.message });
    afficherErreur("Erreur de connexion au serveur : " + err.message);
  } finally {
    btnGenerer.disabled = false;
    btnGenerer.innerHTML = '<span class="btn-text">Générer la fiche</span><span class="btn-icon">✨</span>';
  }
}


/** Affiche une étape dans la liste de progression */
function afficherEtape(etape) {
  const liste = document.getElementById("steps-list");
  const item = document.createElement("div");
  item.className = "step-item";
  item.innerHTML = `
    <span class="step-status">${etape.statut || "⏳"}</span>
    <span class="step-name">${etape.etape}</span>
    ${etape.detail ? `<span class="step-detail">${etape.detail}</span>` : ""}
  `;
  liste.appendChild(item);
  item.scrollIntoView({ behavior: "smooth", block: "nearest" });
}


/** Affiche les résultats après génération réussie */
function afficherResultats(donnees) {
  const card = document.getElementById("results-card");
  card.classList.remove("hidden");

  // Lien Google Docs
  const lien = document.getElementById("link-google-doc");
  lien.href = donnees.lien_doc || "#";

  const nomAffiche = document.getElementById("nom-fichier-display");
  nomAffiche.textContent = donnees.nom_fichier || "Ouvrir dans Google Docs";

  // Aperçu de la fiche
  const apercu = donnees.apercu_fiche || {};

  // Objectifs
  const blocObjectifs = document.getElementById("apercu-objectifs");
  if (apercu.objectifs && apercu.objectifs.length > 0) {
    blocObjectifs.innerHTML = `
      <h4>🎯 Objectifs de la séance</h4>
      <ul>${apercu.objectifs.map(o => `<li>${htmlEchapper(o)}</li>`).join("")}</ul>
    `;
  }

  // Concepts-clés (Nouvelle structure : liste de titres ou texte simple)
  const blocConcepts = document.getElementById("apercu-concepts");
  if (apercu.concepts && apercu.concepts.length > 0) {
    blocConcepts.innerHTML = `
      <h4>💡 Concepts-clés / Sections</h4>
      <ul>${apercu.concepts.map(c => {
        if (typeof c === 'object' && c !== null) {
          return `<li><span class="concept-terme">${htmlEchapper(c.terme || "")}</span><br><span class="concept-def">${htmlEchapper(c.definition || "")}</span></li>`;
        }
        return `<li>${htmlEchapper(c)}</li>`;
      }).join("")}</ul>
    `;
  }

  // Points essentiels
  const blocPoints = document.getElementById("apercu-points");
  if (apercu.points_essentiels && apercu.points_essentiels.length > 0) {
    blocPoints.innerHTML = `
      <h4>✅ Points essentiels</h4>
      <ul>${apercu.points_essentiels.map(p => `<li>${htmlEchapper(p)}</li>`).join("")}</ul>
    `;
  }

  // Ouvrir aperçu automatiquement
  document.getElementById("apercu-section").open = true;

  card.scrollIntoView({ behavior: "smooth", block: "start" });
}


/** Affiche un message d'erreur */
function afficherErreur(message, trace = null) {
  const card = document.getElementById("error-card");
  const msgEl = document.getElementById("error-message");
  const traceEl = document.getElementById("error-trace");

  msgEl.textContent = message || "Une erreur inattendue est survenue.";

  if (trace) {
    traceEl.textContent = trace;
    traceEl.classList.remove("hidden");
  } else {
    traceEl.classList.add("hidden");
  }

  card.classList.remove("hidden");
  card.scrollIntoView({ behavior: "smooth", block: "start" });
}


/** Affiche une erreur inline sur un champ de formulaire */
function afficherErreurChamp(champId, message) {
  const champ = document.getElementById(champId);
  if (champ) {
    champ.focus();
    champ.style.borderColor = "rgba(252, 129, 129, 0.6)";
    setTimeout(() => { champ.style.borderColor = ""; }, 3000);
  }
  alert(message);
}


// ─────────────────────────────────────────────
// Statut système
// ─────────────────────────────────────────────

async function verifierStatut() {
  const textEl = document.getElementById("status-text");
  const dotEl = document.querySelector(".status-dot");

  try {
    const reponse = await fetch("/api/statut");
    const statuts = await reponse.json();

    const tousOk = Object.values(statuts).every(v => v.includes("✅"));
    const geminiOk = statuts.gemini_api?.includes("✅");
    const driveOk = statuts.google_drive?.includes("✅");

    if (tousOk) {
      textEl.textContent = "Tous les systèmes opérationnels ✅";
      dotEl.className = "status-dot";
    } else if (!geminiOk) {
      textEl.textContent = "Clé Gemini manquante ⚠️";
      dotEl.className = "status-dot error";
    } else if (!driveOk) {
      textEl.textContent = "Service Account Drive manquant ⚠️";
      dotEl.className = "status-dot error";
    } else {
      textEl.textContent = "Configuration partielle ⚠️";
      dotEl.className = "status-dot error";
    }
  } catch {
    textEl.textContent = "Serveur inaccessible ❌";
    dotEl.className = "status-dot error";
  }
}


// ─────────────────────────────────────────────
// Utilitaires
// ─────────────────────────────────────────────

/** Vide le contenu d'un élément par son ID */
function nettoyer(id) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = "";
}

/** Échappe le HTML pour éviter les XSS */
function htmlEchapper(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
