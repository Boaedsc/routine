// Affiche la date du jour en français
const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
document.getElementById('date').textContent =
  new Date().toLocaleDateString('fr-FR', options);

// Enregistre le service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js');
}
// Charge la messe du jour depuis messes/AAAA-MM-JJ.json
async function chargerMesseDuJour() {
  const jour = new Date();
  const cle = [
    jour.getFullYear(),
    String(jour.getMonth() + 1).padStart(2, '0'),
    String(jour.getDate()).padStart(2, '0'),
  ].join('-');

  try {
    const r = await fetch(`messes/${cle}.json`);
    if (!r.ok) throw new Error(`Pas de messe pour ${cle}`);
    const m = await r.json();
    document.getElementById('titre-messe').textContent = m.titre;
    document.getElementById('messe-texte').textContent = m.texte;
  } catch (e) {
    document.getElementById('titre-messe').textContent = 'Messe du jour indisponible';
    console.warn(e);
  }
}

chargerMesseDuJour();