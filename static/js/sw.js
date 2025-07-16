/**
 * Service Worker for Fleet Management System
 * Implements offline-first caching strategy for maritime operations
 */

const CACHE_VERSION = 'v2.0.0';
const STATIC_CACHE = `fleet-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `fleet-dynamic-${CACHE_VERSION}`;
const OFFLINE_CACHE = `fleet-offline-${CACHE_VERSION}`;
const OPERATIONS_CACHE = `fleet-operations-${CACHE_VERSION}`;
const MARITIME_CACHE = `fleet-maritime-${CACHE_VERSION}`;
const STEVEDORE_CACHE = `fleet-stevedore-${CACHE_VERSION}`;
const CRITICAL_CACHE = `fleet-critical-${CACHE_VERSION}`;

// Enhanced files to cache immediately (stevedoring app shell)
const STATIC_FILES = [
    '/',
    '/static/css/app.css',
    '/static/css/mobile.css',
    '/static/css/operations-dashboard.css',
    '/static/css/maritime-components.css',
    '/static/css/team-management.css',
    '/static/css/cargo-tracking.css',
    '/static/css/icons.css',
    '/static/js/app.js',
    '/static/js/operations-dashboard.js',
    '/static/js/offline-db.js',
    '/static/js/sync.js',
    '/static/js/vessel-sync.js',
    '/static/icons/icon-72x72.png',
    '/static/icons/icon-96x96.png',
    '/static/icons/icon-128x128.png',
    '/static/icons/icon-144x144.png',
    '/static/icons/icon-152x152.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-384x384.png',
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

// Enhanced maritime operations endpoints for stevedoring
const MARITIME_ENDPOINTS = [
    '/maritime/api/operations',
    '/maritime/berth/status',
    '/api/maritime/teams/performance',
    '/api/maritime/kpis',
    '/api/maritime/alerts/active',
    '/api/maritime/berths/assign',
    '/api/maritime/berths/unassign',
    '/api/maritime/berths/capacity',
    '/api/maritime/vessel/queue',
    '/api/maritime/stevedore/assignments',
    '/api/maritime/cargo/tracking',
    '/api/maritime/weather/conditions',
    '/api/maritime/equipment/status'
];

// Critical stevedoring operations that need immediate caching
const CRITICAL_ENDPOINTS = [
    '/maritime/berth/status',
    '/api/maritime/alerts/active',
    '/api/maritime/vessel/queue',
    '/api/maritime/kpis'
];

// Enhanced critical operations data for stevedoring offline support
const CRITICAL_OPERATIONS = [
    'berth_assignments',
    'vessel_queue',
    'active_operations',
    'team_status',
    'alerts',
    'stevedore_assignments',
    'cargo_operations',
    'equipment_status',
    'weather_conditions',
    'safety_protocols',
    'emergency_contacts'
];

// Enhanced background sync tags for stevedoring operations
const SYNC_TAGS = {
    TASK_SYNC: 'task-sync',
    USER_SYNC: 'user-sync',
    BERTH_ASSIGNMENT: 'berth-assignment-sync',
    OPERATIONS_UPDATE: 'operations-update-sync',
    MARITIME_DATA: 'maritime-data-sync',
    CRITICAL_ALERTS: 'critical-alerts-sync',
    STEVEDORE_ASSIGNMENT: 'stevedore-assignment-sync',
    CARGO_UPDATE: 'cargo-update-sync',
    EQUIPMENT_STATUS: 'equipment-status-sync',
    WEATHER_UPDATE: 'weather-update-sync',
    SAFETY_INCIDENT: 'safety-incident-sync',
    PERFORMANCE_METRICS: 'performance-metrics-sync'
};

// Cache priorities for stevedoring operations
const CACHE_PRIORITIES = {
    CRITICAL: 1,    // Safety, alerts, emergency
    HIGH: 2,        // Berth assignments, vessel queue
    MEDIUM: 3,      // Operations data, team performance
    LOW: 4          // Historical data, reports
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
    
    // Skip non-GET requests and external requests for caching
    if (url.origin !== location.origin) {
        return;
    }
    
    // Handle POST requests for offline queuing
    if (request.method === 'POST' && isMaritimeAPI(url.pathname)) {
        event.respondWith(handleOfflineAction(request));
        return;
    }
    
    // Skip non-GET requests for caching
    if (request.method !== 'GET') {
        return;
    }
    
    // Enhanced request handling with priorities
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirst(request));
    } else if (isCriticalEndpoint(url.pathname)) {
        event.respondWith(criticalNetworkFirst(request));
    } else if (isMaritimeAPI(url.pathname)) {
        event.respondWith(maritimeNetworkFirst(request));
    } else if (isAPIRequest(url.pathname)) {
        event.respondWith(networkFirst(request));
    } else if (isNavigationRequest(request)) {
        event.respondWith(networkFirst(request, '/offline'));
    } else {
        event.respondWith(staleWhileRevalidate(request));
    }
});

// Enhanced background sync for stevedoring operations
self.addEventListener('sync', event => {
    console.log('Background sync triggered:', event.tag);
    
    switch (event.tag) {
        case SYNC_TAGS.TASK_SYNC:
            event.waitUntil(syncTasks());
            break;
        case SYNC_TAGS.USER_SYNC:
            event.waitUntil(syncUserData());
            break;
        case SYNC_TAGS.BERTH_ASSIGNMENT:
            event.waitUntil(syncBerthAssignments());
            break;
        case SYNC_TAGS.OPERATIONS_UPDATE:
            event.waitUntil(syncOperationsUpdates());
            break;
        case SYNC_TAGS.MARITIME_DATA:
            event.waitUntil(syncMaritimeData());
            break;
        case SYNC_TAGS.CRITICAL_ALERTS:
            event.waitUntil(syncCriticalAlerts());
            break;
        case SYNC_TAGS.STEVEDORE_ASSIGNMENT:
            event.waitUntil(syncStevedoreAssignments());
            break;
        case SYNC_TAGS.CARGO_UPDATE:
            event.waitUntil(syncCargoUpdates());
            break;
        case SYNC_TAGS.EQUIPMENT_STATUS:
            event.waitUntil(syncEquipmentStatus());
            break;
        case SYNC_TAGS.WEATHER_UPDATE:
            event.waitUntil(syncWeatherData());
            break;
        case SYNC_TAGS.SAFETY_INCIDENT:
            event.waitUntil(syncSafetyIncidents());
            break;
        case SYNC_TAGS.PERFORMANCE_METRICS:
            event.waitUntil(syncPerformanceMetrics());
            break;
        default:
            console.log('Unknown sync tag:', event.tag);
    }
});

// Enhanced push notification handling for stevedoring operations
self.addEventListener('push', event => {
    console.log('Push notification received');
    
    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data = { title: 'Stevedoring Operations', body: event.data.text() };
        }
    }
    
    // Enhanced notification options for stevedoring operations
    const options = {
        title: data.title || 'Stevedoring Operations',
        body: data.body || 'New notification',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        data: data.data || {},
        actions: getNotificationActions(data.type),
        requireInteraction: isHighPriorityAlert(data),
        vibrate: getVibrationPattern(data.severity),
        tag: data.tag || 'general',
        renotify: data.renotify || false,
        silent: data.silent || false,
        timestamp: Date.now(),
        // Enhanced options for stevedoring
        dir: 'auto',
        lang: 'en',
        image: data.image || null,
        // Custom payload for stevedoring operations
        data: {
            ...data.data,
            timestamp: Date.now(),
            type: data.type,
            priority: data.severity,
            operationId: data.operationId,
            berthNumber: data.berthNumber,
            vesselId: data.vesselId
        }
    };
    
    event.waitUntil(
        Promise.all([
            self.registration.showNotification(options.title, options),
            storeCriticalAlert(data),
            updateNotificationBadge(data.type),
            logNotificationMetrics(data)
        ])
    );
});

// Enhanced notification click handling for stevedoring operations
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event.action, event.notification.data);
    
    event.notification.close();
    
    const data = event.notification.data || {};
    let targetUrl = '/';
    
    // Handle different actions for stevedoring operations
    switch (event.action) {
        case 'view':
            if (data.operationId) {
                targetUrl = `/dashboard/operations?operation=${data.operationId}`;
            } else if (data.berthNumber) {
                targetUrl = `/dashboard/operations?berth=${data.berthNumber}`;
            } else {
                targetUrl = data.url || '/dashboard/operations';
            }
            break;
        case 'acknowledge':
            // Handle alert acknowledgment
            event.waitUntil(acknowledgeAlert(data.alertId));
            return;
        case 'escalate':
            targetUrl = `/dashboard/operations?alert=${data.alertId}&action=escalate`;
            break;
        case 'manage':
            if (data.berthNumber) {
                targetUrl = `/dashboard/operations?berth=${data.berthNumber}&action=manage`;
            }
            break;
        case 'update':
            if (data.operationId) {
                targetUrl = `/maritime/ship_operations/${data.operationId}/update`;
            }
            break;
        default:
            // Default click action
            if (data.operationId) {
                targetUrl = `/dashboard/operations?operation=${data.operationId}`;
            } else if (data.url) {
                targetUrl = data.url;
            } else {
                targetUrl = '/dashboard/operations';
            }
    }
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clientList => {
                // Try to focus existing window first
                for (const client of clientList) {
                    if (client.url.includes('/dashboard') && 'focus' in client) {
                        client.focus();
                        client.postMessage({
                            type: 'NOTIFICATION_CLICK',
                            action: event.action,
                            data: data,
                            targetUrl: targetUrl
                        });
                        return;
                    }
                }
                
                // Open new window if no existing window found
                return clients.openWindow(targetUrl);
            })
    );
});

// Helper functions

function isStaticAsset(pathname) {
    return pathname.startsWith('/static/') || 
           pathname.includes('.css') || 
           pathname.includes('.js') || 
           pathname.includes('.png') || 
           pathname.includes('.jpg') || 
           pathname.includes('.ico') ||
           pathname.includes('.svg') ||
           pathname.includes('.woff') ||
           pathname.includes('.woff2') ||
           pathname === '/manifest.json' ||
           pathname === '/favicon.ico';
}

function isCriticalEndpoint(pathname) {
    return CRITICAL_ENDPOINTS.some(endpoint => pathname.startsWith(endpoint));
}

function isAPIRequest(pathname) {
    return pathname.startsWith('/api/');
}

function isMaritimeAPI(pathname) {
    return pathname.startsWith('/maritime/') || 
           pathname.startsWith('/api/maritime/') ||
           pathname.includes('/stevedore/') ||
           pathname.includes('/cargo/') ||
           pathname.includes('/berth/') ||
           MARITIME_ENDPOINTS.some(endpoint => pathname.startsWith(endpoint));
}

function isNavigationRequest(request) {
    return request.mode === 'navigate' || 
           (request.method === 'GET' && 
            request.headers.get('accept') && 
            request.headers.get('accept').includes('text/html'));
}

// Enhanced critical endpoint caching strategy\nasync function criticalNetworkFirst(request) {\n    const url = new URL(request.url);\n    \n    try {\n        const networkResponse = await fetch(request);\n        \n        if (networkResponse.ok) {\n            const cache = await caches.open(CRITICAL_CACHE);\n            // Clone and cache immediately for critical data\n            cache.put(request, networkResponse.clone());\n            \n            // Also update maritime cache for consistency\n            const maritimeCache = await caches.open(MARITIME_CACHE);\n            const responseClone = networkResponse.clone();\n            const responseData = await responseClone.json();\n            \n            const cachedData = {\n                data: responseData,\n                timestamp: Date.now(),\n                url: request.url,\n                critical: true,\n                priority: CACHE_PRIORITIES.CRITICAL\n            };\n            \n            maritimeCache.put(request, new Response(JSON.stringify(cachedData), {\n                headers: networkResponse.headers\n            }));\n            \n            return networkResponse;\n        }\n        \n        throw new Error('Network response not ok');\n    } catch (error) {\n        console.log('Critical endpoint network request failed, trying cache:', request.url);\n        \n        // Try critical cache first\n        let cachedResponse = await caches.match(request, { cacheName: CRITICAL_CACHE });\n        \n        if (!cachedResponse) {\n            // Fallback to maritime cache\n            cachedResponse = await caches.match(request, { cacheName: MARITIME_CACHE });\n        }\n        \n        if (cachedResponse) {\n            try {\n                const cachedData = await cachedResponse.json();\n                const age = Date.now() - cachedData.timestamp;\n                \n                // Critical data is valid for only 2 minutes when offline\n                const maxAge = 2 * 60 * 1000;\n                \n                if (age < maxAge) {\n                    return new Response(JSON.stringify(cachedData.data), {\n                        headers: { 'Content-Type': 'application/json' }\n                    });\n                }\n                \n                // Return stale data with warning for critical endpoints\n                cachedData.data._offline = true;\n                cachedData.data._stale = true;\n                cachedData.data._age = age;\n                \n                return new Response(JSON.stringify(cachedData.data), {\n                    headers: { 'Content-Type': 'application/json' }\n                });\n            } catch (e) {\n                // Cached response is not JSON, return as is\n                return cachedResponse;\n            }\n        }\n        \n        return new Response(JSON.stringify({ \n            error: 'Critical data unavailable', \n            message: 'No cached critical data available',\n            offline: true\n        }), { \n            status: 503, \n            statusText: 'Service Unavailable',\n            headers: { 'Content-Type': 'application/json' }\n        });\n    }\n}\n\n// Handle offline actions for stevedoring operations\nasync function handleOfflineAction(request) {\n    const url = new URL(request.url);\n    \n    if (!navigator.onLine) {\n        // Queue the action for later sync\n        const actionData = {\n            id: Date.now().toString(),\n            url: request.url,\n            method: request.method,\n            headers: Object.fromEntries(request.headers.entries()),\n            body: await request.text(),\n            timestamp: Date.now(),\n            retryCount: 0\n        };\n        \n        try {\n            const db = await openOfflineDB();\n            const transaction = db.transaction(['offline_actions'], 'readwrite');\n            const store = transaction.objectStore('offline_actions');\n            await store.put(actionData);\n            \n            console.log('Action queued for offline sync:', actionData.url);\n            \n            // Schedule background sync\n            if ('serviceWorker' in self && 'sync' in self.ServiceWorkerRegistration.prototype) {\n                const syncTag = getSyncTagForAction(url.pathname);\n                await self.registration.sync.register(syncTag);\n            }\n            \n            return new Response(JSON.stringify({\n                success: true,\n                message: 'Action queued for sync when online',\n                queued: true,\n                actionId: actionData.id\n            }), {\n                status: 202,\n                headers: { 'Content-Type': 'application/json' }\n            });\n        } catch (error) {\n            console.error('Failed to queue offline action:', error);\n            \n            return new Response(JSON.stringify({\n                success: false,\n                error: 'Failed to queue action for offline sync',\n                offline: true\n            }), {\n                status: 503,\n                headers: { 'Content-Type': 'application/json' }\n            });\n        }\n    } else {\n        // Online - forward the request normally\n        return fetch(request);\n    }\n}\n\nfunction getSyncTagForAction(pathname) {\n    if (pathname.includes('/berth/assign') || pathname.includes('/berth/unassign')) {\n        return SYNC_TAGS.BERTH_ASSIGNMENT;\n    } else if (pathname.includes('/stevedore/')) {\n        return SYNC_TAGS.STEVEDORE_ASSIGNMENT;\n    } else if (pathname.includes('/cargo/')) {\n        return SYNC_TAGS.CARGO_UPDATE;\n    } else if (pathname.includes('/equipment/')) {\n        return SYNC_TAGS.EQUIPMENT_STATUS;\n    } else if (pathname.includes('/alert')) {\n        return SYNC_TAGS.CRITICAL_ALERTS;\n    } else {\n        return SYNC_TAGS.OPERATIONS_UPDATE;\n    }\n}\n\n// Enhanced maritime-specific caching strategy
async function maritimeNetworkFirst(request) {
    const url = new URL(request.url);
    const isCriticalOperation = CRITICAL_OPERATIONS.some(op => 
        url.pathname.includes(op) || url.searchParams.get('operation') === op
    );
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(MARITIME_CACHE);
            // Store with timestamp for freshness checks
            const responseClone = networkResponse.clone();
            const responseData = await responseClone.json();
            
            const cachedData = {
                data: responseData,
                timestamp: Date.now(),
                url: request.url,
                critical: isCriticalOperation
            };
            
            cache.put(request, new Response(JSON.stringify(cachedData), {
                headers: networkResponse.headers
            }));
            
            return networkResponse;
        }
        
        throw new Error('Network response not ok');
    } catch (error) {
        console.log('Maritime network request failed, trying cache:', request.url);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            const cachedData = await cachedResponse.json();
            const age = Date.now() - cachedData.timestamp;
            
            // Use cached data if less than 5 minutes old for critical operations
            // or 30 minutes for non-critical
            const maxAge = isCriticalOperation ? 5 * 60 * 1000 : 30 * 60 * 1000;
            
            if (age < maxAge) {
                return new Response(JSON.stringify(cachedData.data), {
                    headers: { 'Content-Type': 'application/json' }
                });
            }
        }
        
        // Return stale data with offline indicator
        if (cachedResponse) {
            const cachedData = await cachedResponse.json();
            cachedData.data._offline = true;
            cachedData.data._stale = true;
            
            return new Response(JSON.stringify(cachedData.data), {
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        return new Response(JSON.stringify({ 
            error: 'Offline', 
            message: 'No cached data available' 
        }), { 
            status: 503, 
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'application/json' }
        });
    }
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

// Enhanced maritime sync functions

async function syncBerthAssignments() {
    try {
        console.log('Starting berth assignment synchronization...');
        
        const db = await openOfflineDB();
        const transaction = db.transaction(['berth_assignments'], 'readonly');
        const store = transaction.objectStore('berth_assignments');
        const pendingAssignments = await getAllFromStore(store);
        
        for (const assignment of pendingAssignments) {
            try {
                const response = await fetch('/maritime/berth/assign', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(assignment.data)
                });
                
                if (response.ok) {
                    // Remove from offline queue
                    const deleteTransaction = db.transaction(['berth_assignments'], 'readwrite');
                    const deleteStore = deleteTransaction.objectStore('berth_assignments');
                    await deleteStore.delete(assignment.id);
                    
                    console.log('Berth assignment synced:', assignment.id);
                } else {
                    console.error('Berth assignment sync failed:', response.status);
                }
            } catch (error) {
                console.error('Error syncing berth assignment:', assignment.id, error);
            }
        }
        
        console.log('Berth assignment synchronization completed');
    } catch (error) {
        console.error('Berth assignment synchronization failed:', error);
        throw error;
    }
}

async function syncOperationsUpdates() {
    try {
        console.log('Starting operations updates synchronization...');
        
        const db = await openOfflineDB();
        const transaction = db.transaction(['operations_updates'], 'readonly');
        const store = transaction.objectStore('operations_updates');
        const pendingUpdates = await getAllFromStore(store);
        
        for (const update of pendingUpdates) {
            try {
                const response = await fetch('/maritime/api/operations/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(update.data)
                });
                
                if (response.ok) {
                    const deleteTransaction = db.transaction(['operations_updates'], 'readwrite');
                    const deleteStore = deleteTransaction.objectStore('operations_updates');
                    await deleteStore.delete(update.id);
                    
                    console.log('Operations update synced:', update.id);
                } else {
                    console.error('Operations update sync failed:', response.status);
                }
            } catch (error) {
                console.error('Error syncing operations update:', update.id, error);
            }
        }
        
        console.log('Operations updates synchronization completed');
    } catch (error) {
        console.error('Operations updates synchronization failed:', error);
        throw error;
    }
}

async function syncMaritimeData() {
    try {
        console.log('Starting maritime data synchronization...');
        
        // Sync all maritime-related data
        const endpoints = [
            '/maritime/api/operations',
            '/maritime/berth/status',
            '/api/maritime/teams/performance',
            '/api/maritime/kpis'
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint);
                if (response.ok) {
                    const data = await response.json();
                    const cache = await caches.open(MARITIME_CACHE);
                    
                    const cachedData = {
                        data: data,
                        timestamp: Date.now(),
                        url: endpoint,
                        critical: true
                    };
                    
                    cache.put(endpoint, new Response(JSON.stringify(cachedData), {
                        headers: { 'Content-Type': 'application/json' }
                    }));
                    
                    console.log('Maritime data cached:', endpoint);
                }
            } catch (error) {
                console.error('Error syncing maritime data:', endpoint, error);
            }
        }
        
        console.log('Maritime data synchronization completed');
    } catch (error) {
        console.error('Maritime data synchronization failed:', error);
        throw error;
    }
}

async function syncCriticalAlerts() {
    try {
        console.log('Starting critical alerts synchronization...');
        
        const db = await openOfflineDB();
        const transaction = db.transaction(['critical_alerts'], 'readonly');
        const store = transaction.objectStore('critical_alerts');
        const pendingAlerts = await getAllFromStore(store);
        
        for (const alert of pendingAlerts) {
            try {
                const response = await fetch('/api/maritime/alerts/sync', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(alert.data)
                });
                
                if (response.ok) {
                    const deleteTransaction = db.transaction(['critical_alerts'], 'readwrite');
                    const deleteStore = deleteTransaction.objectStore('critical_alerts');
                    await deleteStore.delete(alert.id);
                    
                    console.log('Critical alert synced:', alert.id);
                } else {
                    console.error('Critical alert sync failed:', response.status);
                }
            } catch (error) {
                console.error('Error syncing critical alert:', alert.id, error);
            }
        }
        
        console.log('Critical alerts synchronization completed');
    } catch (error) {
        console.error('Critical alerts synchronization failed:', error);
        throw error;
    }
}

// Enhanced notification functions

function getNotificationActions(type) {
    switch (type) {
        case 'berth_assignment':
            return [
                { action: 'view', title: 'View Berth', icon: '/static/icons/view.png' },
                { action: 'manage', title: 'Manage', icon: '/static/icons/settings.png' }
            ];
        case 'critical_alert':
            return [
                { action: 'acknowledge', title: 'Acknowledge', icon: '/static/icons/check.png' },
                { action: 'escalate', title: 'Escalate', icon: '/static/icons/warning.png' }
            ];
        case 'operation_update':
            return [
                { action: 'view', title: 'View Operation', icon: '/static/icons/view.png' },
                { action: 'update', title: 'Update Status', icon: '/static/icons/edit.png' }
            ];
        default:
            return [
                { action: 'view', title: 'View', icon: '/static/icons/view.png' },
                { action: 'dismiss', title: 'Dismiss', icon: '/static/icons/dismiss.png' }
            ];
    }
}

function isHighPriorityAlert(data) {
    return data.severity === 'critical' || 
           data.severity === 'urgent' ||
           data.type === 'critical_alert' ||
           data.requireInteraction === true;
}

function getVibrationPattern(severity) {
    switch (severity) {
        case 'critical':
            return [200, 100, 200, 100, 200, 100, 200];
        case 'urgent':
            return [300, 100, 300, 100, 300];
        case 'warning':
            return [200, 100, 200];
        case 'info':
            return [100, 50, 100];
        default:
            return [200, 100, 200];
    }
}

async function storeCriticalAlert(data) {
    if (data.severity === 'critical' || data.type === 'critical_alert') {
        try {
            const db = await openOfflineDB();
            const transaction = db.transaction(['critical_alerts'], 'readwrite');
            const store = transaction.objectStore('critical_alerts');
            
            const alertData = {
                id: Date.now().toString(),
                data: data,
                timestamp: Date.now(),
                acknowledged: false
            };
            
            await store.put(alertData);
            console.log('Critical alert stored offline:', alertData.id);
        } catch (error) {
            console.error('Error storing critical alert:', error);
        }
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
            
            // Maritime-specific stores
            if (!db.objectStoreNames.contains('berth_assignments')) {
                db.createObjectStore('berth_assignments', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('operations_updates')) {
                db.createObjectStore('operations_updates', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('critical_alerts')) {
                db.createObjectStore('critical_alerts', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('maritime_data')) {
                db.createObjectStore('maritime_data', { keyPath: 'key' });
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