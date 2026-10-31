// Cache versionné : incrémenter CACHE à chaque mise à jour des fichiers statiques.
var CACHE = 'routine-v7';
var STATIC = ['./', 'index.html', 'style.css', 'app.js', 'manifest.json'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(STATIC); }));
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
  if (url.origin !== location.origin) return; // polices, Cloudflare… non gérés ici

  e.respondWith(
    fetch(e.request)
      .then(function (rep) {
        // On met en cache les statiques, les JSON de messe et les mp3 (réponses OK uniquement)
        if (rep.ok) {
          var copie = rep.clone();
          caches.open(CACHE).then(function (c) { c.put(e.request, copie); });
        }
        return rep;
      })
      .catch(function () { return caches.match(e.request); })
  );
});