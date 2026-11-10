// app.js â€” affiche la ou les messes d'une date Ã  partir du JSON produit par messe.py.
(function () {
  'use strict';

  var BASE_JSON = 'messes';
  var BASE_PDF = 'partitions';
  var PDF_WORKER = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
  var ORDRE = ['Introitus', 'Lectio', 'Graduale', 'Tractus', 'Alleluia',
               'Evangelium', 'Offertorium', 'Communio'];
  var TITRES = {
    Introitus: 'Introït', Lectio: 'Épître', Graduale: 'Graduel',
    Tractus: 'Trait', Alleluia: 'Alléluia', Evangelium: 'Évangile',
    Offertorium: 'Offertoire', Communio: 'Communion',
  };
  // Sections toujours en français uniquement
  var FR_SEULEMENT = ['Lectio', 'Evangelium'];
  // Sections avec partition PDF attendue
  var AVEC_PARTITION = ['Introitus', 'Graduale', 'Tractus', 'Alleluia', 'Offertorium', 'Communio'];

  var cacheExistence = {};

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

  // MÃªme logique que generer_messe.py : minuscules, sans accents, tirets
  function slug(s) {
    return String(s || '')
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function nomPdf(cle, incipit) {
    var s = slug(incipit);
    if (!s) return null;
    return BASE_PDF + '/' + slug(cle) + '_' + s + '.pdf';
  }

  // Vérifie l'existence d'un PDF (résultat mis en cache)
  function pdfExiste(chemin) {
    if (chemin in cacheExistence) return Promise.resolve(cacheExistence[chemin]);
    return fetch(encodeURI(chemin), { method: 'HEAD' })
      .then(function (r) { cacheExistence[chemin] = r.ok; return r.ok; })
      .catch(function () { cacheExistence[chemin] = false; return false; });
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

  // Corrige les références et la reprise de l'antienne dans l'introït.
  function corrigerIntroitus(t) {
    var lignes = t.split('\n');
    if (lignes.length < 2) return t;

    for (var i = 1; i < lignes.length; i++) {
      var m = lignes[i].match(/^\s*!?\s*(Ps\.?\s+.+?)\s*$/i);
      if (!m) continue;
      var psaume = m[1].replace(/[.!?]+\s*$/, '').trim();
      var origine = lignes[0].replace(/^\s*!\s*/, '').replace(/[.!?]+\s*$/, '').trim();
      if (psaume && origine) lignes[0] = '!' + origine + '; ' + psaume;
      lignes.splice(i, 1);
      break;
    }

    var gloria = lignes.findIndex(function (ligne) {
      return /^\s*Gloria Patri\s*$/i.test(ligne);
    });
    var premiereAntienne = lignes[1] && lignes[1].trim();
    var derniere = lignes.length - 1;
    if (gloria !== -1 && derniere > gloria && premiereAntienne &&
        lignes[derniere].trim() === premiereAntienne) {
      lignes.splice(derniere, 1);
    }
    return lignes.join('\n');
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

function construireTexte(brut, classeLangue, estPsaume) {
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
    c.className = 'corps' + (estPsaume ? ' psaume' : '');
    c.textContent = d.corps;
    conteneur.appendChild(c);
  }
  return conteneur;
}

  // Partition : rendu PDF.js de la 1re page, recadré sur la zone de notation
  function ajouterPartition(block, cle, incipit) {
    if (AVEC_PARTITION.indexOf(cle) === -1) return;
    var chemin = nomPdf(cle, incipit);
    if (!chemin) return;

    pdfExiste(chemin).then(function (ok) {
      if (!ok || !window.pdfjsLib) return;

      var canvas = document.createElement('canvas');
      canvas.className = 'pdf';
      canvas.setAttribute('role', 'img');
      canvas.setAttribute('aria-label', 'Partition ' + (TITRES[cle] || cle));

      var wrap = document.createElement('div');
      wrap.className = 'partition';
      wrap.appendChild(canvas);
      block.appendChild(wrap);

      rendrePartition(encodeURI(chemin), canvas, wrap);
    });
  }

  function rendrePartition(url, canvas, wrap) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = PDF_WORKER;

    pdfjsLib.getDocument(url).promise
      .then(function (pdf) { return pdf.getPage(1); })
      .then(function (page) {
        var vue = page.getViewport({ scale: 2 }); // rendu net sur écran retina
        var tmp = document.createElement('canvas');
        tmp.width = vue.width;
        tmp.height = vue.height;
        return page.render({ canvasContext: tmp.getContext('2d'), viewport: vue }).promise
          .then(function () { return recadrer(tmp); });
      })
      .then(function (rogne) {
        canvas.width = rogne.width;
        canvas.height = rogne.height;
        canvas.getContext('2d').drawImage(rogne, 0, 0);
      })
      .catch(function () { wrap.remove(); });
  }
  // Lit une variable CSS (ex. --carte) telle qu'elle est actuellement appliquée
  function couleurCss(nom) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(nom).trim();
    var m = v.match(/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
    if (!m) return null;
    return [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)];
  }
  // Recadre la partition et applique les couleurs du thème :
  // fond = --carte, encres = --texte. Les pixels intermédiaires (anti-aliasing)
  // sont interpolés entre les deux couleurs, ce qui garde des contours nets.
  function recadrer(src) {
    var fond = (couleurCss('--carte') || [255, 255, 255])
      .map(function (c) { return Math.round(c + (255 - c) * 0.35); });
    var encre = couleurCss('--texte') || [0, 0, 0];

    var ctx = src.getContext('2d');
    var img = ctx.getImageData(0, 0, src.width, src.height);
    var d = img.data;
    var x0 = src.width, y0 = src.height, x1 = 0, y1 = 0;

    for (var y = 0; y < src.height; y++) {
      for (var x = 0; x < src.width; x++) {
        var i = (y * src.width + x) * 4;
        // LuminositÃ© du pixel d'origine : 1 = blanc, 0 = noir
        var l = (d[i] + d[i + 1] + d[i + 2]) / (3 * 255);

        d[i]     = encre[0] + (fond[0] - encre[0]) * l;
        d[i + 1] = encre[1] + (fond[1] - encre[1]) * l;
        d[i + 2] = encre[2] + (fond[2] - encre[2]) * l;
        d[i + 3] = 255;

        if (l < 0.97) {
          if (x < x0) x0 = x;
          if (x > x1) x1 = x;
          if (y < y0) y0 = y;
          if (y > y1) y1 = y;
        }
      }
    }
    ctx.putImageData(img, 0, 0);

    if (x1 <= x0 || y1 <= y0) return src;

    var pad = 8;
    x0 = Math.max(0, x0 - pad);
    y0 = Math.max(0, y0 - pad);
    x1 = Math.min(src.width, x1 + pad);
    y1 = Math.min(src.height, y1 + pad);

    var out = document.createElement('canvas');
    out.width = x1 - x0;
    out.height = y1 - y0;
    out.getContext('2d').drawImage(src, x0, y0, out.width, out.height, 0, 0, out.width, out.height);
    return out;
}
  // Pour Lectio et Evangelium, on retire la premiÃ¨re ligne du texte
  function retirerPremiereLigne(brut) {
    var lignes = brut.split('\n');
    return lignes.slice(1).join('\n');
}

  function renderSection(cle, fr, la) {
    var frTexte = nettoyer(fr && fr.texte);
    var laTexte = nettoyer(la && la.texte);
    if (cle === 'Introitus') {
      frTexte = frTexte && corrigerIntroitus(frTexte);
      laTexte = laTexte && corrigerIntroitus(laTexte);
    }

    if (FR_SEULEMENT.indexOf(cle) !== -1) {
      frTexte = retirerPremiereLigne(frTexte);
      laTexte = retirerPremiereLigne(laTexte);
    }

    if (!frTexte && !laTexte) return null;
    var estPsaume = cle === 'Introitus' || cle === 'Graduale' || cle === 'Tractus' ||
                    cle === 'Offertorium' || cle === 'Communio';

    var block = document.createElement('section');
    block.className = 'section';
    block.setAttribute('data-cle', cle);

    var bilingue = FR_SEULEMENT.indexOf(cle) === -1 && laTexte && frTexte;
    var estPsaume = cle === 'Introitus' || cle === 'Graduale' || cle === 'Tractus' ||
                    cle === 'Offertorium' || cle === 'Communio';

    var block = document.createElement('section');
    block.className = 'section';
    block.setAttribute('data-cle', cle);

    var h = document.createElement('h3');
    h.textContent = TITRES[cle] || cle;
    block.appendChild(h);

    // Incipit : celui de la langue latine en prioritÃ© (c'est lui qui nomme le PDF)
    var incipit = (la && la.incipit && la.incipit.incipit) ||
                  (fr && fr.incipit && fr.incipit.incipit) || '';

    if (bilingue) {
      var pile = document.createElement('div');
      pile.className = 'pile langue-fr';
      pile.appendChild(construireTexte(frTexte, 'texte-fr', estPsaume));
      pile.appendChild(construireTexte(laTexte, 'texte-la', estPsaume));
      block.appendChild(pile);

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'bascule';
      btn.textContent = 'LA';
      btn.setAttribute('aria-label', 'Basculer entre franÃ§ais et latin');
      btn.addEventListener('click', function () {
        var estFr = pile.classList.toggle('langue-fr');
        pile.classList.toggle('langue-la', !estFr);
        btn.textContent = estFr ? 'LA' : 'FR';
      });
      block.appendChild(btn);
    } else {
      block.appendChild(construireTexte(frTexte || laTexte,
                                        frTexte ? 'texte-fr' : 'texte-la', estPsaume));
    }

    // Audio : chemin relatif, erreur silencieuse si absent
    var mp3 = (la && la.mp3) || (fr && fr.mp3);
    if (texteOk(mp3)) {
      var chemin = 'Graduale Project/' + mp3.replace(/^\/+/, '');
      var wrapAudio = document.createElement('div');
      wrapAudio.className = 'audio';
      var audio = document.createElement('audio');
      audio.controls = true;
      audio.preload = 'none';
      audio.src = encodeURI(chemin);
      audio.addEventListener('error', function () {
        wrapAudio.classList.add('audio-indispo');
        wrapAudio.title = 'Fichier audio introuvable : ' + chemin;
      });
      wrapAudio.appendChild(audio);
      block.appendChild(wrapAudio);
    }

    ajouterPartition(block, cle, incipit);
    return block;
  }

  function renderMesse(messe) {
    var zone = $('messe');
    zone.textContent = '';

    var occ = messe.occurrence || {};
    $('titre').textContent = occ.nom_sanctoral || occ.gagnant || '';

    var meta = [];
    if (occ.commemorations && occ.commemorations.length) {
      meta.push('commÃ©moration' + (occ.commemorations.length > 1 ? 's' : '') + ' : ' +
                occ.commemorations.join(', '));
    }
    $('meta').textContent = meta.join(' â€” ');

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
      var nom = (m.occurrence && (m.occurrence.nom_sanctoral || m.occurrence.gagnant)) ||
                ('Messe ' + (i + 1));
      opt.textContent = (m.numero || i + 1) + ' â€” ' + nom;
      select.appendChild(opt);
    });

    wrap.hidden = messes.length < 2;
    select.onchange = function () { renderMesse(messes[Number(select.value)]); };
    renderMesse(messes[0]);
  }

  function loadDate(dateStr) {
    $('titre').textContent = 'Chargementâ€¦';
    $('meta').textContent = '';
    $('messe').textContent = '';
    $('choix-messe-wrap').hidden = true;

    fetch(BASE_JSON + '/' + dateStr + '.json', { cache: 'no-cache' })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(renderJour)
      .catch(function (err) {
        $('titre').textContent = '';
        $('meta').textContent = '';
        showError('Impossible de charger la messe du ' + dateStr +
                  ' (' + (err && err.message ? err.message : 'erreur inconnue') + ').');
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