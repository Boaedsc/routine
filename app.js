// app.js — affiche la ou les messes d'une date à partir du JSON produit par messe.py.
// Vanilla JS, aucune dépendance.
(function () {
  'use strict';

  var BASE_JSON = 'messes';
  // Ordre d'affichage des sections de la messe (aligné sur PARTS de messe.py)
  var ORDRE = ['Introitus', 'Oratio', 'Lectio', 'Graduale', 'Tractus', 'Alleluia',
               'Evangelium', 'Offertorium', 'Secreta', 'Prefatio', 'Communio', 'Postcommunio'];
  var TITRES = {
    Introitus: 'Introït', Oratio: 'Collecte', Lectio: 'Épître', Graduale: 'Graduel',
    Tractus: 'Trait', Alleluia: 'Alléluia', Evangelium: 'Évangile', Offertorium: 'Offertoire',
    Secreta: 'Secrète', Prefatio: 'Préface', Communio: 'Communion', Postcommunio: 'Postcommunion'
  };

  var $ = function (id) { return document.getElementById(id); };

  function formatDateFR(d) {
    return d.toLocaleDateString('fr-FR', {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });
  }

  function isoDate(d) {
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var j = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + m + '-' + j;
  }

  function showError(message) {
    var zone = $('messe');
    zone.textContent = '';
    var err = document.createElement('div');
    err.className = 'erreur';
    err.setAttribute('role', 'alert');
    err.textContent = message;
    zone.appendChild(err);
  }

  // Un texte est "utile" s'il est non vide après trim
  function texteOk(t) {
    return typeof t === 'string' && t.trim().length > 0;
  }

  // Construit un bloc de section : titre, incipit, mp3, puis texte(s)
  function renderSection(cle, fr, la) {
    var frTexte = fr && texteOk(fr.texte) ? fr.texte : '';
    var laTexte = la && texteOk(la.texte) ? la.texte : '';
    if (!frTexte && !laTexte) return null; // rien à afficher

    var block = document.createElement('section');
    block.className = 'section';
    block.setAttribute('data-cle', cle);

    var h = document.createElement('h3');
    h.textContent = TITRES[cle] || cle;
    block.appendChild(h);

    // Incipit : juste après le titre, dans la section
    var inc = (fr && fr.incipit) || (la && la.incipit);
    if (texteOk(inc)) {
      var pInc = document.createElement('p');
      pInc.className = 'incipit';
      pInc.textContent = inc;
      block.appendChild(pInc);
    }

    // Audio : juste après l'incipit
    var mp3 = (fr && fr.mp3) || (la && la.mp3);
    if (texteOk(mp3)) {
      var wrap = document.createElement('div');
      wrap.className = 'audio';
      var audio = document.createElement('audio');
      audio.controls = true;
      audio.preload = 'none';
      audio.src = mp3;
      wrap.appendChild(audio);
      block.appendChild(wrap);
    }

    // Textes : français puis latin (si différent), en paragraphes distincts
    if (frTexte) {
      var pFr = document.createElement('p');
      pFr.className = 'texte texte-fr';
      pFr.textContent = frTexte;
      block.appendChild(pFr);
    }
    if (laTexte && laTexte !== frTexte) {
      var pLa = document.createElement('p');
      pLa.className = 'texte texte-la';
      pLa.textContent = laTexte;
      block.appendChild(pLa);
    }

    return block;
  }

  function renderMesse(messe) {
    var zone = $('messe');
    zone.textContent = '';

    var occ = messe.occurrence || {};
    var titre = $('titre');
    titre.textContent = occ.nom_sanctoral || occ.gagnant || '';

    var meta = [];
    if (occ.classe != null) meta.push('classe ' + occ.classe);
    if (occ.commemorations && occ.commemorations.length) {
      meta.push('commémoration' + (occ.commemorations.length > 1 ? 's' : '') + ' : '
                + occ.commemorations.join(', '));
    }
    $('meta').textContent = meta.join(' — ');

    var sec = messe.sections || {};
    var fr = sec.Francais || {};
    var la = sec.Latin || {};

    var rendu = 0;
    ORDRE.forEach(function (cle) {
      var bloc = renderSection(cle, fr[cle], la[cle]);
      if (bloc) { zone.appendChild(bloc); rendu++; }
    });

    if (rendu === 0) showError('Aucun texte disponible pour cette messe.');
  }

  // Remplit le sélecteur et affiche la messe n° choisie
  function renderJour(data) {
    var messes = Array.isArray(data.messes) ? data.messes : [];
    var wrap = $('choix-messe-wrap');
    var select = $('choix-messe');

    if (messes.length === 0) {
      showError('Aucune messe pour cette date.');
      wrap.hidden = true;
      return;
    }

    select.textContent = '';
    messes.forEach(function (m, i) {
      var opt = document.createElement('option');
      opt.value = String(i);
      var nom = (m.occurrence && (m.occurrence.nom_sanctoral || m.occurrence.gagnant)) || ('Messe ' + (i + 1));
      opt.textContent = 'Messe ' + (m.numero || i + 1) + ' — ' + nom;
      select.appendChild(opt);
    });

    wrap.hidden = messes.length < 2;
    select.onchange = function () { renderMesse(messes[Number(select.value)]); };
    renderMesse(messes[0]);
  }

  function loadDate(dateStr) {
    $('titre').textContent = 'Chargement…';
    $('meta').textContent = '';
    $('messe').textContent = '';
    $('choix-messe-wrap').hidden = true;

    var url = BASE_JSON + '/' + dateStr + '.json';
    fetch(url, { cache: 'no-cache' })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (data) {
        renderJour(data);
      })
      .catch(function (err) {
        $('titre').textContent = '';
        showError('Impossible de charger la messe du ' + dateStr
                  + ' (' + (err && err.message ? err.message : 'erreur inconnue') + ').');
      });
  }

  function init() {
    $('date').textContent = formatDateFR(new Date());

    var picker = $('date-picker');
    var today = isoDate(new Date());
    picker.value = today;
    picker.addEventListener('change', function () {
      if (picker.value) loadDate(picker.value);
    });

    loadDate(today);

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('sw.js').catch(function () {});
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();