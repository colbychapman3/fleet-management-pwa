// Enhanced Service Worker for PWA with stale-while-revalidate strategy
const CACHE_NAME = 'fleet-management-v1';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/manifest.json',
    '/offline'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache).catch(error => {
                    console.error('Failed to cache all resources:', error);
                });
            })
    );
});

self.addEventListener('fetch', event => {
    // Only handle http/https requests, skip chrome-extension and other schemes
    if (!event.request.url.startsWith('http://') && !event.request.url.startsWith('https://')) {
        return;
    }
    
    // Skip caching for chrome-extension and other non-http schemes
    if (event.request.url.includes('chrome-extension://')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                // Stale-while-revalidate strategy
                const fetchPromise = fetch(event.request).then(
                    networkResponse => {
                        // Check if we received a valid response and URL is cacheable
                        if (networkResponse && 
                            networkResponse.status === 200 && 
                            networkResponse.type === 'basic' &&
                            (event.request.url.startsWith('http://') || event.request.url.startsWith('https://'))) {
                            
                            const responseToCache = networkResponse.clone();
                            caches.open(CACHE_NAME)
                                .then(cache => {
                                    try {
                                        cache.put(event.request, responseToCache);
                                    } catch (error) {
                                        console.log('Cache put failed:', error);
                                    }
                                });
                        }
                        return networkResponse;
                    }
                ).catch(error => {
                    console.log('Fetch failed:', error);
                    // Return offline page for navigation requests
                    if (event.request.mode === 'navigate') {
                        return caches.match('/offline');
                    }
                });

                return cachedResponse || fetchPromise;
            })
    );
});