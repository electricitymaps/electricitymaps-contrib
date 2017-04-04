var CACHE_NAME = 'my-site-cache-v1';
// Here we should cache all static assets to ensure offline mode
var urlsToCache = [
  '/',
  'dist/bundle.dev.js',
  'dist/styles.dev.css'
];

console.log(serviceWorkerOption)

self.addEventListener('install', function(event) {
  // Perform install steps
  // Warning: anything that fails here will prevent installation
  // of the service worker
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Cache hit - return response
        if (response) {
          console.log('Cache hit ', event.request);
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Happens when a new service worker is activated (after installation)
self.addEventListener('activate', function(event) {

  var cacheWhitelist = ['my-site-cache-v1'];

  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
