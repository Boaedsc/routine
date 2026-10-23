// Affiche la date du jour en français
const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
document.getElementById('date').textContent =
  new Date().toLocaleDateString('fr-FR', options);

// Enregistre le service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js');
}
