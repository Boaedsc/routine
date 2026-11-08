// Cache versionné : incrémenter CACHE à chaque mise à jour des fichiers statiques.
var CACHE = 'routine-v12';
var STATIC = ['./', 'index.html', 'style.css', 'app.js', 'manifest.json'];
// Bibliothèques externes utiles hors ligne
var EXTERNES = [
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'
];

// Ressources lourdes ou volatiles : mises en cache à la demande uniquement.
function ressourceCachable(url) {
  return url.pathname.indexOf('/messes/') !== -1 ||
         url.pathname.indexOf('/partitions/') !== -1 ||
         /\.(json|pdf)$/i.test(url.pathname) ||
         STATIC.some(function (s) { return url.pathname.endsWith(s.replace('./', '/')); });
}

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return c.addAll(STATIC.concat(EXTERNES));
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (cles) {
      return Promise.all(cles.filter(function (c) { return c !== CACHE; })
                             .map(function (c) { return caches.delete(c); }));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  var url = new URL(e.request.url);

  // Bibliothèques externes : cache d'abord (elles ne changent pas)
  if (EXTERNES.indexOf(e.request.url) !== -1) {
    e.respondWith(
      caches.match(e.request).then(function (hit) {
        return hit || fetch(e.request).then(function (rep) {
          var copie = rep.clone();
          caches.open(CACHE).then(function (c) { c.put(e.request, copie); });
          return rep;
        });
      })
    );
    return;
  }

  if (url.origin !== location.origin) return;

  // Les mp3 ne sont pas mis en cache (volumineux) : réseau direct.
  if (/\.mp3$/i.test(url.pathname)) return;

  e.respondWith(
    fetch(e.request)
      .then(function (rep) {
        if (rep.ok && ressourceCachable(url)) {
          var copie = rep.clone();
          caches.open(CACHE).then(function (c) { c.put(e.request, copie); });
        }
        return rep;
      })
      .catch(function () { return caches.match(e.request); })
  );
});