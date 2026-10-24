// Affiche la date du jour en français
const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
document.getElementById('date').textContent =
  new Date().toLocaleDateString('fr-FR', options);

// Enregistre le service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js');
}

// Sections : [clé dans le JSON, titre affiché, afficher le latin ?]
const SECTIONS = [
  ['Introitus',    'Introït',    true],
  ['Lectio',       'Lecture',    false],
  ['Graduale',     'Graduel',    true],
  ['Evangelium',   'Évangile',   false],
  ['Offertorium',  'Offertoire', true],
  ['Communio',     'Communion',  true],
];

// Cherche une clé sans tenir compte de la casse
function trouver(obj, cle) {
  if (!obj || typeof obj !== 'object') return undefined;
  const k = Object.keys(obj).find(x => x.toLowerCase() === cle.toLowerCase());
  return k ? obj[k] : undefined;
}

// Transforme les "\n" littéraux (backslash + n) en vrais retours à la ligne
function nettoyer(s) {
  if (typeof s !== 'string') return s;
  return s
    .replace(/\\r\\n/g, '\n')
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, ' ')
    .replace(/\\"/g, '"');
}

function construireTexte(m) {
  const blocs = [];
  for (const [cle, titre, avecLatin] of SECTIONS) {
    const fr = nettoyer(trouver(m.francais, cle));
    const la = nettoyer(trouver(m.latin, cle));
    if (!fr && !la) continue;
    let bloc = `— ${titre} —\n`;
    if (avecLatin && la) bloc += `${la}\n\n`;
    if (fr) bloc += fr;
    blocs.push(bloc.trim());
  }
  return blocs.join('\n\n');
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
    console.log('Clés du JSON :', Object.keys(m), m);

    titre.textContent = m.titre || m.nom || 'Messe du jour';
    texte.textContent = construireTexte(m) || nettoyer(JSON.stringify(m, null, 2));
  } catch (e) {
    titre.textContent = 'Messe du jour indisponible';
    texte.textContent = '';
    console.warn(e);
  }
}

chargerMesseDuJour();