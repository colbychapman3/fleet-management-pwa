// Enhanced Service Worker for PWA with stale-while-revalidate strategy
const CACHE_NAME = 'fleet-management-v2';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/manifest.json',
    '/offline',
    '/favicon.ico'
];

self.addEventListener('install', event => {
    console.log('Service Worker v2 installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache v2');
                // Cache resources one by one to avoid failures
                return Promise.allSettled(
                    urlsToCache.map(url => 
                        cache.add(url).catch(error => {
                            console.warn(`Failed to cache ${url}:`, error);
                            return null; // Continue with other resources
                        })
                    )
                );
            })
            .then(() => {
                console.log('Service Worker v2 installation complete');
                // Force activation of new service worker
                return self.skipWaiting();
            })
    );
});

// Force immediate activation when new SW is ready
self.addEventListener('activate', event => {
    console.log('Service Worker v2 activating...');
    event.waitUntil(
        // Clear old caches
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker v2 activated');
            return self.clients.claim();
        })
    );
});

self.addEventListener('fetch', event => {
    const url = event.request.url;
    
    // Skip non-HTTP requests completely
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        return;
    }
    
    // Skip chrome-extension, moz-extension, and other browser extension schemes
    if (url.includes('chrome-extension://') || 
        url.includes('moz-extension://') || 
        url.includes('safari-extension://') ||
        url.includes('extension://')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                // Return cached version if available
                if (cachedResponse) {
                    return cachedResponse;
                }
                
                // Fetch from network
                return fetch(event.request).then(networkResponse => {
                    // Only cache successful responses from our domain
                    if (networkResponse && 
                        networkResponse.status === 200 && 
                        networkResponse.type === 'basic' &&
                        url.startsWith(self.location.origin)) {
                        
                        const responseToCache = networkResponse.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                try {
                                    cache.put(event.request, responseToCache);
                                } catch (error) {
                                    console.warn('Cache put failed for:', url, error);
                                }
                            })
                            .catch(error => {
                                console.warn('Cache open failed:', error);
                            });
                    }
                    return networkResponse;
                }).catch(error => {
                    console.log('Fetch failed for:', url, error);
                    // Return offline page for navigation requests
                    if (event.request.mode === 'navigate') {
                        return caches.match('/offline');
                    }
                    throw error;
                });
            })
            .catch(error => {
                console.warn('Cache match failed for:', url, error);
                return fetch(event.request);
            })
    );
});