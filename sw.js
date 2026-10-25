
const CACHE = 'routine-v5';          // incrémenter pour forcer la mise à jour
const FILES = ['./', 'index.html', 'style.css', 'app.js', 'manifest.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(clés =>
      Promise.all(clés.filter(c => c !== CACHE).map(c => caches.delete(c)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  const estMesse = url.pathname.includes('/messes/');

  e.respondWith(
    caches.match(e.request).then(r => {
      if (r) return r;
      return fetch(e.request).then(rep => {
        if (estMesse && rep.ok) {
          const copie = rep.clone();
          caches.open(CACHE).then(c => c.put(e.request, copie));
        }
        return rep;
      });
    })
  );
});