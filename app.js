// app.js — affiche la messe d'une date donnée à partir d'un JSON
// produit par messe.py. Vanilla JS, aucune dépendance.
//
// Format JSON attendu (voir la description de la tâche) :
// {
//   "date": "YYYY-MM-DD",
//   "celebration": { "nom": "...", "classe": N, "note": "..." },
//   "fichiers": [...],
//   "cles_jour": [...],
//   "sections": [
//     { "cle": "...", "titre": "...",
//       "textes":  { "Francais": "...", "Latin": "..." },   // Latin optionnel
//       "audios":  "chemin/relatif.mp3" | null }
//   ]
// }

(function () {
  'use strict';

  // Dossier où messe.py dépose les JSON. À adapter si besoin.
  var BASE_JSON = 'messes';

  var $ = function (id) { return document.getElementById(id); };

  function formatDateFR(d) {
    return d.toLocaleDateString('fr-FR', {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });
  }

  function isoDate(d) {
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var j = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + j;
  }

  function setText(el, text) {
    if (el) el.textContent = (text == null) ? '' : String(text);
  }

  function clearZone() {
    var zone = $('messe');
    if (zone) zone.textContent = '';
  }

  function showError(message) {
    clearZone();
    var zone = $('messe');
    if (!zone) return;
    var err = document.createElement('div');
    err.className = 'erreur';
    err.setAttribute('role', 'alert');
    // textContent → pas besoin d'échappement HTML manuel
    err.textContent = message;
    zone.appendChild(err);
  }

  function renderSection(container, sec) {
    var textes = (sec && sec.textes) || {};
    var hasLatin = !!textes.Latin;
    var hasFrancais = !!textes.Francais;
    if (!hasLatin && !hasFrancais) return; // section vide : on n'affiche rien

    // Mode courant : français en priorité, sinon latin
    var mode = hasFrancais ? 'Francais' : 'Latin';

    var block = document.createElement('section');
    block.className = 'section';
    block.setAttribute('data-cle', sec.cle || '');

    var h = document.createElement('h3');
    h.textContent = sec.titre || sec.cle || '';
    block.appendChild(h);

    var textesEl = document.createElement('div');
    textesEl.className = 'textes';
    block.appendChild(textesEl);

    function paint() {
      textesEl.textContent = '';
      var contenu = textes[mode];
      if (contenu) {
        var p = document.createElement('p');
        p.className = 'texte';
        // textContent : échapper HTML n'est pas nécessaire, c'est fait par le DOM
        p.textContent = contenu;
        textesEl.appendChild(p);
      }
    }

    // Bouton d'alternance uniquement quand les deux langues existent
    if (hasLatin && hasFrancais) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'toggle-langue';
      btn.textContent = 'Voir en latin';
      btn.addEventListener('click', function () {
        mode = (mode === 'Francais') ? 'Latin' : 'Francais';
        btn.textContent = (mode === 'Latin') ? 'Voir en français' : 'Voir en latin';
        paint();
      });
      block.appendChild(btn);
    }

    paint();

    // Audio : string → lecteur, null → rien
    var audios = sec.audios;
    if (typeof audios === 'string' && audios.length > 0) {
      var audioWrap = document.createElement('div');
      audioWrap.className = 'audio';
      var audio = document.createElement('audio');
      audio.controls = true;
      audio.preload = 'none';
      // src est assigné via propriété : le navigateur encode les espaces / caractères spéciaux
      audio.src = audios;
      audioWrap.appendChild(audio);
      block.appendChild(audioWrap);
    }
    // audios === null (ou manquant) → pas de lecteur

    container.appendChild(block);
  }

  function render(data) {
    var titreEl = $('titre');
    var noteEl = $('note');
    var zone = $('messe');
    if (!zone) return;

    clearZone();

    var celeb = (data && data.celebration) || {};
    var nom = celeb.nom || '';
    setText(titreEl, nom);

    if (celeb.classe != null && titreEl) {
      var classeEl = document.createElement('span');
      classeEl.className = 'classe';
      classeEl.textContent = ' (classe ' + celeb.classe + ')';
      titreEl.appendChild(classeEl);
    }
    setText(noteEl, celeb.note || '');

    var sections = (data && Array.isArray(data.sections)) ? data.sections : [];
    if (sections.length === 0) {
      showError('Aucune section disponible pour cette date.');
      return;
    }
    sections.forEach(function (sec) { renderSection(zone, sec); });
  }

  function loadDate(dateStr) {
    setText($('titre'), 'Chargement…');
    setText($('note'), '');
    clearZone();

    var url = BASE_JSON + '/' + dateStr + '.json';

    fetch(url, { cache: 'no-cache' })
      .then(function (res) {
        if (!res.ok) {
          throw new Error('HTTP ' + res.status + ' sur ' + url);
        }
        return res.json();
      })
      .then(function (data) {
        render(data);
      })
      .catch(function (err) {
        setText($('titre'), '');
        showError("Impossible de charger la messe du " + dateStr
                  + " (" + (err && err.message ? err.message : 'erreur inconnue') + ").");
      });
  }

  function init() {
    // Bandeau date du jour
    var dateEl = $('date');
    if (dateEl) dateEl.textContent = formatDateFR(new Date());

    // Sélecteur de date
    var picker = $('date-picker');
    var today = isoDate(new Date());
    if (picker) {
      picker.value = today;
      picker.addEventListener('change', function () {
        if (picker.value) loadDate(picker.value);
      });
    }

    loadDate(today);

    // Service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('sw.js').catch(function () { /* ignore */ });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
