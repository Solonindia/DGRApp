// static/service-worker.js
const SW_VERSION = 'v1.0.1';
const PRECACHE = `precache-${SW_VERSION}`;
const RUNTIME = `runtime-${SW_VERSION}`;

// Important: all URLs must exist and match Django static paths
const PRECACHE_URLS = [
  '/',  // homepage
  '/offline',  // fallback page served by Django
  '/static/manifest.webmanifest',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  // Add any CSS or JS files essential for first render
  // '/static/css/main.css',
  // '/static/js/app.js',
];

// INSTALL: pre-cache essential assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(PRECACHE).then(cache => {
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

// ACTIVATE: cleanup old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys
          .filter(k => (k.startsWith('precache-') || k.startsWith('runtime-')) && k !== PRECACHE && k !== RUNTIME)
          .map(k => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

// FETCH: serve cached content, fallback to network
self.addEventListener('fetch', event => {
  const req = event.request;

  // Only handle GET and same-origin requests
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) {
    return;
  }

  // Navigation requests (HTML)
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then(res => {
          const resClone = res.clone();
          caches.open(RUNTIME).then(cache => cache.put(req, resClone));
          return res;
        })
        .catch(async () => {
          const cached = await caches.match(req);
          return cached || caches.match('/offline');
        })
    );
    return;
  }

  // Static assets: Stale-While-Revalidate strategy
  event.respondWith(
    caches.match(req).then(cached => {
      const networkFetch = fetch(req)
        .then(networkRes => {
          if (networkRes && networkRes.status === 200) {
            const clone = networkRes.clone();
            caches.open(RUNTIME).then(cache => cache.put(req, clone));
          }
          return networkRes;
        })
        .catch(() => cached);
      return cached || networkFetch;
    })
  );
});
