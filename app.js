// app.js — affiche la ou les messes d'une date à partir du JSON produit par messe.py.
(function () {
  'use strict';

  var BASE_JSON = 'messes';
  var ORDRE = ['Introitus', 'Lectio', 'Graduale', 'Tractus', 'Alleluia',
               'Evangelium', 'Offertorium', 'Communio'];
  var TITRES = {
    Introitus: 'Introït', Lectio: 'Épître', Graduale: 'Graduel',
    Tractus: 'Trait', Alleluia: 'Alléluia', Evangelium: 'Évangile',
    Offertorium: 'Offertoire', Communio: 'Communion'
  };
  // Sections toujours en français uniquement
  var FR_SEULEMENT = ['Lectio', 'Evangelium'];
  // Sections où l'incipit n'est pas affiché
  var SANS_INCIPIT = ['Introitus', 'Lectio', 'Graduale', 'Tractus', 'Alleluia',
                      'Evangelium', 'Offertorium', 'Communio'];

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

  function texteOk(t) {
    return typeof t === 'string' && t.trim().length > 0;
  }

  // Nettoie les marqueurs de rubrique du texte source
  function nettoyer(t) {
    if (!texteOk(t)) return '';
    return t
      .split('\n')
      .map(function (ligne) {
        return ligne
          .replace(/^\s*&Gloria\s*$/, 'Gloria Patri')
          .replace(/^\s*\$/, '');
      })
      .join('\n')
      .trim();
  }

  // Sépare l'origine (ligne commençant par "!") du corps du texte
  function decouper(t) {
    var lignes = t.split('\n');
    var origine = '';
    if (lignes.length && /^\s*!/.test(lignes[0])) {
      origine = lignes.shift().replace(/^\s*!\s*/, '').trim();
    }
    return { origine: origine, corps: lignes.join('\n').trim() };
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

  // Construit le bloc texte (origine + corps), utilisé pour FR et LA
  function construireTexte(brut, classeLangue) {
    var d = decouper(brut);
    var conteneur = document.createElement('div');
    conteneur.className = 'texte ' + classeLangue;

    if (d.origine) {
      var o = document.createElement('p');
      o.className = 'origine';
      o.textContent = d.origine;
      conteneur.appendChild(o);
    }

    if (d.corps) {
      var c = document.createElement('p');
      c.className = 'corps';
      c.textContent = d.corps;
      conteneur.appendChild(c);
    }
    return conteneur;
  }

  function renderSection(cle, fr, la) {
    var frTexte = nettoyer(fr && fr.texte);
    var laTexte = nettoyer(la && la.texte);
    if (!frTexte && !laTexte) return null;

    var bilingue = FR_SEULEMENT.indexOf(cle) === -1 && laTexte && frTexte;

    var block = document.createElement('section');
    block.className = 'section';
    block.setAttribute('data-cle', cle);

    var h = document.createElement('h3');
    h.textContent = TITRES[cle] || cle;
    block.appendChild(h);

    // Incipit : seulement si la section ne fait pas partie de SANS_INCIPIT
    if (SANS_INCIPIT.indexOf(cle) === -1) {
      var inc = nettoyer((fr && fr.incipit) || (la && la.incipit));
      if (inc) {
        var pInc = document.createElement('p');
        pInc.className = 'incipit';
        pInc.textContent = inc;
        block.appendChild(pInc);
      }
    }

    if (bilingue) {
      // Superposition FR / LA, bascule par bouton
      var pile = document.createElement('div');
      pile.className = 'pile langue-fr';
      pile.appendChild(construireTexte(frTexte, 'texte-fr'));
      pile.appendChild(construireTexte(laTexte, 'texte-la'));
      block.appendChild(pile);

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'bascule';
      btn.textContent = 'LA';
      btn.setAttribute('aria-label', 'Basculer entre français et latin');
      btn.addEventListener('click', function () {
        var estFr = pile.classList.toggle('langue-fr');
        pile.classList.toggle('langue-la', !estFr);
        btn.textContent = estFr ? 'LA' : 'FR';
      });
      block.appendChild(btn);
    } else {
      // Français seul (Lectio, Evangelium) ou latin seul en secours
      block.appendChild(construireTexte(frTexte || laTexte, frTexte ? 'texte-fr' : 'texte-la'));
    }

    // Audio en dernier
    var mp3 = (fr && fr.mp3) || (la && la.mp3);
    if (texteOk(mp3)) {
      var dossierAudio = 'Graduale Project/';
      var chemin = dossierAudio + mp3.replace(/^\/+/, '');
      var src = encodeURI(chemin);
      var wrap = document.createElement('div');
      wrap.className = 'audio';
      var audio = document.createElement('audio');
      audio.controls = true;
      audio.preload = 'metadata';
      audio.src = src;
      audio.addEventListener('error', function () {
        wrap.classList.add('audio-indispo');
        wrap.setAttribute('title', 'Fichier audio introuvable : ' + chemin);
      });
      wrap.appendChild(audio);
      block.appendChild(wrap);
    }

    return block;
  }

  function renderMesse(messe) {
    var zone = $('messe');
    zone.textContent = '';

    var occ = messe.occurrence || {};
    $('titre').textContent = occ.nom_sanctoral || occ.gagnant || '';

    var meta = [];
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
      .then(renderJour)
      .catch(function (err) {
        $('titre').textContent = '';
        $('meta').textContent = '';
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