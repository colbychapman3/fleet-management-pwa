/**
 * Service Worker for Fleet Management System
 * Implements offline-first caching strategy for maritime operations
 */

const CACHE_VERSION = 'v1.0.0';
const STATIC_CACHE = `fleet-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `fleet-dynamic-${CACHE_VERSION}`;
const OFFLINE_CACHE = `fleet-offline-${CACHE_VERSION}`;

// Files to cache immediately (app shell)
const STATIC_FILES = [
    '/',
    '/static/css/app.css',
    '/static/css/offline.css',
    '/static/js/app.js',
    '/static/js/offline-db.js',
    '/static/js/sync.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/offline',
    '/manifest.json'
];

// API endpoints to cache with network-first strategy
const API_ENDPOINTS = [
    '/api/tasks',
    '/api/vessels',
    '/api/users',
    '/api/dashboard/stats'
];

// Background sync tags
const SYNC_TAGS = {
    TASK_SYNC: 'task-sync',
    USER_SYNC: 'user-sync'
};

self.addEventListener('install', event => {
    console.log('Service Worker installing...', CACHE_VERSION);
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Caching app shell files');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('App shell cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Failed to cache app shell:', error);
            })
    );
});

self.addEventListener('activate', event => {
    console.log('Service Worker activating...', CACHE_VERSION);
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        // Delete old caches
                        if (cacheName.startsWith('fleet-') && 
                            !cacheName.includes(CACHE_VERSION)) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Old caches cleaned up');
                return self.clients.claim();
            })
    );
});

self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests and external requests
    if (request.method !== 'GET' || url.origin !== location.origin) {
        return;
    }
    
    // Handle different types of requests
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirst(request));
    } else if (isAPIRequest(url.pathname)) {
        event.respondWith(networkFirst(request));
    } else if (isNavigationRequest(request)) {
        event.respondWith(networkFirst(request, '/offline'));
    } else {
        event.respondWith(staleWhileRevalidate(request));
    }
});

// Background sync for offline operations
self.addEventListener('sync', event => {
    console.log('Background sync triggered:', event.tag);
    
    switch (event.tag) {
        case SYNC_TAGS.TASK_SYNC:
            event.waitUntil(syncTasks());
            break;
        case SYNC_TAGS.USER_SYNC:
            event.waitUntil(syncUserData());
            break;
        default:
            console.log('Unknown sync tag:', event.tag);
    }
});

// Push notification handling
self.addEventListener('push', event => {
    console.log('Push notification received');
    
    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data = { title: 'Fleet Management', body: event.data.text() };
        }
    }
    
    const options = {
        title: data.title || 'Fleet Management',
        body: data.body || 'New notification',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        data: data.data || {},
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/static/icons/view.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/icons/dismiss.png'
            }
        ],
        requireInteraction: data.requireInteraction || false,
        vibrate: [200, 100, 200]
    };
    
    event.waitUntil(
        self.registration.showNotification(options.title, options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event.action);
    
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow(event.notification.data.url || '/')
        );
    }
});

// Helper functions

function isStaticAsset(pathname) {
    return pathname.startsWith('/static/') || 
           pathname.includes('.css') || 
           pathname.includes('.js') || 
           pathname.includes('.png') || 
           pathname.includes('.jpg') || 
           pathname.includes('.ico') ||
           pathname === '/manifest.json';
}

function isAPIRequest(pathname) {
    return pathname.startsWith('/api/');
}

function isNavigationRequest(request) {
    return request.mode === 'navigate' || 
           (request.method === 'GET' && 
            request.headers.get('accept') && 
            request.headers.get('accept').includes('text/html'));
}

// Cache strategies

async function cacheFirst(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.error('Cache first strategy failed:', error);
        return caches.match('/offline');
    }
}

async function networkFirst(request, fallbackUrl = null) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error('Network response not ok');
    } catch (error) {
        console.log('Network request failed, trying cache:', request.url);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        if (fallbackUrl) {
            return caches.match(fallbackUrl);
        }
        
        return new Response('Offline', { 
            status: 503, 
            statusText: 'Service Unavailable' 
        });
    }
}

async function staleWhileRevalidate(request) {
    const cachedResponse = await caches.match(request);
    
    const fetchPromise = fetch(request).then(networkResponse => {
        if (networkResponse.ok) {
            const cache = caches.open(DYNAMIC_CACHE);
            cache.then(c => c.put(request, networkResponse.clone()));
        }
        return networkResponse;
    }).catch(error => {
        console.error('Stale while revalidate fetch failed:', error);
        return cachedResponse;
    });
    
    return cachedResponse || fetchPromise;
}

// Background sync functions

async function syncTasks() {
    try {
        console.log('Starting task synchronization...');
        
        // Get pending task changes from IndexedDB
        const db = await openOfflineDB();
        const transaction = db.transaction(['sync_queue'], 'readonly');
        const store = transaction.objectStore('sync_queue');
        const pendingTasks = await getAllFromStore(store);
        
        for (const task of pendingTasks) {
            try {
                const response = await fetch('/api/sync', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        changes: [task]
                    })
                });
                
                if (response.ok) {
                    // Remove from sync queue on successful sync
                    const deleteTransaction = db.transaction(['sync_queue'], 'readwrite');
                    const deleteStore = deleteTransaction.objectStore('sync_queue');
                    await deleteStore.delete(task.id);
                    
                    console.log('Task synced successfully:', task.id);
                } else {
                    console.error('Task sync failed:', response.status);
                }
            } catch (error) {
                console.error('Error syncing task:', task.id, error);
            }
        }
        
        console.log('Task synchronization completed');
    } catch (error) {
        console.error('Task synchronization failed:', error);
        throw error;
    }
}

async function syncUserData() {
    try {
        console.log('Starting user data synchronization...');
        
        // Sync user profile changes
        const response = await fetch('/api/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                changes: [] // User profile changes would be included here
            })
        });
        
        if (response.ok) {
            console.log('User data synchronized successfully');
        } else {
            console.error('User data sync failed:', response.status);
            throw new Error('User sync failed');
        }
    } catch (error) {
        console.error('User data synchronization failed:', error);
        throw error;
    }
}

// IndexedDB helper functions

function openOfflineDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('FleetOfflineDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Create stores if they don't exist
            if (!db.objectStoreNames.contains('tasks')) {
                db.createObjectStore('tasks', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('sync_queue')) {
                db.createObjectStore('sync_queue', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('cached_data')) {
                db.createObjectStore('cached_data', { keyPath: 'key' });
            }
        };
    });
}

function getAllFromStore(store) {
    return new Promise((resolve, reject) => {
        const request = store.getAll();
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

// Message handling for communication with main thread
self.addEventListener('message', event => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
        case 'GET_VERSION':
            event.ports[0].postMessage({ version: CACHE_VERSION });
            break;
        case 'CACHE_URLS':
            event.waitUntil(
                caches.open(DYNAMIC_CACHE)
                    .then(cache => cache.addAll(data.urls))
                    .then(() => event.ports[0].postMessage({ success: true }))
                    .catch(error => event.ports[0].postMessage({ success: false, error }))
            );
            break;
        case 'CLEAR_CACHE':
            event.waitUntil(
                caches.delete(data.cacheName || DYNAMIC_CACHE)
                    .then(() => event.ports[0].postMessage({ success: true }))
                    .catch(error => event.ports[0].postMessage({ success: false, error }))
            );
            break;
        default:
            console.log('Unknown message type:', type);
    }
});

console.log('Service Worker loaded successfully', CACHE_VERSION);