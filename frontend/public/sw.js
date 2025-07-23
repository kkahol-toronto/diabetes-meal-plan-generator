// Diabetes Meal Plan Generator Service Worker
// Implements caching strategies for offline functionality

const CACHE_NAME = 'diabetes-app-v1.2.0';
const API_CACHE_NAME = 'diabetes-api-cache-v1.0.0';

// Files to cache for offline access
const STATIC_CACHE_URLS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/dietra_logo.png',
  // Add other critical static assets
  '/photos/middle-eastern-cooking-meze-2025-02-12-05-24-20-utc.jpg',
  '/photos/portion-cups-of-healthy-ingredients-on-wooden-tabl-2025-04-03-08-07-00-utc.jpg',
  '/photos/top-view-tasty-salad-with-greens-on-dark-backgroun-2025-02-10-08-46-48-utc.jpg',
  '/photos/vegetarian-buddha-s-bowl-a-mix-of-vegetables-2024-10-18-02-08-30-utc.jpg'
];

// API endpoints to cache for offline access
const API_CACHE_URLS = [
  '/user/welcome-message',
  '/consumption/history',
  '/meal-plans',
  '/user/profile'
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    Promise.all([
      // Cache static assets
      caches.open(CACHE_NAME).then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_CACHE_URLS);
      }),
      // Cache API responses
      caches.open(API_CACHE_NAME).then((cache) => {
        console.log('[SW] Preparing API cache');
        return cache;
      })
    ]).then(() => {
      console.log('[SW] Installation complete');
      // Force activation of new service worker
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Delete old caches
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Activation complete');
      // Take control of all clients
      return self.clients.claim();
    })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/') || isAPIEndpoint(url.pathname)) {
    event.respondWith(networkFirstStrategy(event.request));
  }
  // Handle static assets with cache-first strategy
  else if (event.request.destination === 'script' || 
           event.request.destination === 'style' || 
           event.request.destination === 'image' ||
           STATIC_CACHE_URLS.includes(url.pathname)) {
    event.respondWith(cacheFirstStrategy(event.request));
  }
  // Handle navigation requests with network-first, fallback to cache
  else if (event.request.mode === 'navigate') {
    event.respondWith(navigationStrategy(event.request));
  }
  // Default strategy for other requests
  else {
    event.respondWith(networkFirstStrategy(event.request));
  }
});

// Network-first strategy for API calls
async function networkFirstStrategy(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);
    
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // No cache available, return offline page or error
    return createOfflineResponse(request);
  }
}

// Cache-first strategy for static assets
async function cacheFirstStrategy(request) {
  // Try cache first
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    // Cache miss, fetch from network
    const networkResponse = await fetch(request);
    
    // Cache the response
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[SW] Failed to fetch static asset:', request.url);
    return createOfflineResponse(request);
  }
}

// Navigation strategy for page requests
async function navigationStrategy(request) {
  try {
    // Try network first for navigation
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.log('[SW] Navigation network failed, serving cached app');
    
    // Serve cached index.html for offline navigation
    const cachedApp = await caches.match('/');
    if (cachedApp) {
      return cachedApp;
    }
    
    return createOfflineResponse(request);
  }
}

// Create offline response
function createOfflineResponse(request) {
  if (request.destination === 'document') {
    // Return cached app shell for navigation requests
    return caches.match('/').then(response => 
      response || new Response('App offline. Please check your connection.', {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'text/html' }
      })
    );
  }
  
  // Return generic offline response for other requests
  return new Response(JSON.stringify({
    error: 'Offline',
    message: 'This feature requires an internet connection'
  }), {
    status: 503,
    statusText: 'Service Unavailable',
    headers: { 'Content-Type': 'application/json' }
  });
}

// Helper function to identify API endpoints
function isAPIEndpoint(pathname) {
  const apiPaths = [
    '/user/',
    '/meal-plans',
    '/consumption/',
    '/chat/',
    '/admin/',
    '/recipes',
    '/shopping-lists'
  ];
  
  return apiPaths.some(path => pathname.startsWith(path));
}

// Background sync for offline data synchronization
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'sync-consumption-logs') {
    event.waitUntil(syncConsumptionLogs());
  } else if (event.tag === 'sync-meal-plans') {
    event.waitUntil(syncMealPlans());
  }
});

// Sync offline consumption logs when back online
async function syncConsumptionLogs() {
  try {
    console.log('[SW] Syncing offline consumption logs...');
    
    // Get pending logs from IndexedDB (implement if using IndexedDB for offline storage)
    const pendingLogs = await getPendingConsumptionLogs();
    
    for (const log of pendingLogs) {
      try {
        const response = await fetch('/api/consumption/log', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(log)
        });
        
        if (response.ok) {
          await removePendingLog(log.id);
          console.log('[SW] Synced consumption log:', log.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync log:', log.id, error);
      }
    }
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

// Push notification event handler
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  if (!event.data) {
    return;
  }
  
  try {
    const data = event.data.json();
    
    const options = {
      body: data.body || 'You have a new notification',
      icon: '/dietra_logo.png',
      badge: '/dietra_logo.png',
      tag: data.tag || 'diabetes-app-notification',
      data: data.data || {},
      actions: [
        {
          action: 'view',
          title: 'View',
          icon: '/dietra_logo.png'
        },
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ],
      requireInteraction: data.requireInteraction || false,
      silent: data.silent || false
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'Diabetes App', options)
    );
  } catch (error) {
    console.error('[SW] Push notification error:', error);
    
    // Fallback notification
    event.waitUntil(
      self.registration.showNotification('Diabetes App', {
        body: 'You have a new notification',
        icon: '/dietra_logo.png'
      })
    );
  }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.notification.tag);
  
  event.notification.close();
  
  if (event.action === 'dismiss') {
    return;
  }
  
  // Handle notification click
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Try to focus existing window
      for (let client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          return client.focus();
        }
      }
      
      // Open new window if no existing window found
      if (clients.openWindow) {
        const targetUrl = event.notification.data?.url || '/';
        return clients.openWindow(targetUrl);
      }
    })
  );
});

// Helper functions for offline storage (implement as needed)
async function getPendingConsumptionLogs() {
  // Implement IndexedDB or localStorage logic to retrieve pending logs
  return [];
}

async function removePendingLog(logId) {
  // Implement logic to remove synced log from offline storage
  console.log('[SW] Removing synced log:', logId);
}

async function syncMealPlans() {
  // Implement meal plan synchronization
  console.log('[SW] Syncing meal plans...');
}

// Cache update notification
self.addEventListener('message', (event) => {
  if (event.data?.type === 'CACHE_UPDATE') {
    console.log('[SW] Received cache update request');
    
    event.waitUntil(
      caches.open(API_CACHE_NAME).then(cache => {
        return cache.delete(event.data.url);
      })
    );
  }
});

console.log('[SW] Service worker script loaded'); 