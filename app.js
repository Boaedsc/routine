// Affiche la date du jour en français
const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
document.getElementById('date').textContent =
  new Date().toLocaleDateString('fr-FR', options);

// Enregistre le service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js');
}

// Titres de sections reconnus
const TITRES = ['Introït', 'Lecture', 'Épître', 'Graduel', 'Trait', 'Séquence',
                'Évangile', 'Offertoire', 'Secrète', 'Préface', 'Communion',
                'Postcommunion', 'Oraison', 'Collecte'];

function echapper(s) {
  return s.replace(/&/g, '&').replace(/</g, '<').replace(/>/g, '>');
}

// Met en forme une ligne de texte
function formaterLigne(ligne) {
  const l = ligne.trim();
  if (!l) return '';

  // Renvoi interne (ex: @Sancti/10-02:Communio) : on masque
  if (l.startsWith('@')) return '';

  // Rappel du Gloria Patri
  if (l === '&Gloria') return '<p class="gloria">Gloria Patri…</p>';

  // Référence biblique
  if (l.startsWith('!')) {
    return `<p class="ref">${echapper(l.slice(1).trim().replace(/\.$/, ''))}</p>`;
  }

  // Verset
  const v = l.match(/^[vV]\.\s*(.*)$/);
  if (v) return `<p class="verset"><span class="v">℣.</span> ${echapper(v[1])}</p>`;

  return `<p>${echapper(l)}</p>`;
}

// Découpe le texte brut en sections et génère le HTML
function construireHTML(brut) {
  const lignes = brut.replace(/\r\n/g, '\n').split('\n');
  let html = '';
  let sectionOuverte = false;

  for (const ligne of lignes) {
    const t = ligne.trim();
    if (TITRES.includes(t)) {
      if (sectionOuverte) html += '</section>';
      html += `<section class="partie"><h3>${t}</h3>`;
      sectionOuverte = true;
    } else if (t === '') {
      html += '<div class="espace"></div>';
    } else {
      html += formaterLigne(t);
    }
  }
  if (sectionOuverte) html += '</section>';
  return html;
}

// Charge la messe du jour depuis messes/AAAA-MM-JJ.json
async function chargerMesseDuJour() {
  const jour = new Date();
  const cle = [
    jour.getFullYear(),
    String(jour.getMonth() + 1).padStart(2, '0'),
    String(jour.getDate()).padStart(2, '0'),
  ].join('-');

  const titre = document.getElementById('titre-messe');
  const texte = document.getElementById('messe-texte');

  try {
    const r = await fetch(`messes/${cle}.json`, { cache: 'no-cache' });
    if (!r.ok) throw new Error(`Pas de messe pour ${cle}`);
    const m = await r.json();

    titre.textContent = m.titre || 'Messe du jour';
    texte.innerHTML = construireHTML(m.texte || '');
  } catch (e) {
    titre.textContent = 'Messe du jour indisponible';
    texte.innerHTML = '';
    console.warn(e);
  }
}

chargerMesseDuJour();