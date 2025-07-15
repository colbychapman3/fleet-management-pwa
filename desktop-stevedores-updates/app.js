/**
 * Main application JavaScript
 * Handles PWA initialization, offline functionality, and UI interactions
 */

class FleetApp {
    constructor() {
        this.isOnline = navigator.onLine;
        this.offlineDB = null;
        this.syncManager = null;
        this.serviceWorker = null;
        this.notificationPermission = 'default';
        
        this.init();
    }

    async init() {
        console.log('Initializing Fleet Management App...');
        
        try {
            // Initialize offline database
            this.offlineDB = new OfflineDB();
            await this.offlineDB.init();
            
            // Initialize sync manager
            this.syncManager = new SyncManager(this.offlineDB);
            
            // Register service worker
            await this.registerServiceWorker();
            
            // Setup UI event listeners
            this.setupEventListeners();
            
            // Setup connectivity indicators
            this.setupConnectivityIndicators();
            
            // Request notification permission
            await this.requestNotificationPermission();
            
            // Initialize UI based on current page
            this.initializePage();
            
            console.log('Fleet Management App initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Failed to initialize application');
        }
    }

    // Service Worker management

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('Service Worker registered:', registration);
                
                this.serviceWorker = registration;
                
                // Listen for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    if (newWorker) {
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                this.showUpdateAvailable();
                            }
                        });
                    }
                });
                
                // Listen for messages from service worker
                navigator.serviceWorker.addEventListener('message', event => {
                    this.handleServiceWorkerMessage(event.data);
                });
                
                return registration;
            } catch (error) {
                console.error('Service Worker registration failed:', error);
                throw error;
            }
        } else {
            console.warn('Service Workers not supported');
            return null;
        }
    }

    handleServiceWorkerMessage(data) {
        const { type, payload } = data;
        
        switch (type) {
            case 'SYNC_COMPLETE':
                this.updateSyncStatus();
                this.showNotification('Data synchronized successfully', 'success');
                break;
            case 'SYNC_FAILED':
                this.showNotification('Synchronization failed', 'error');
                break;
            case 'CACHE_UPDATED':
                console.log('Cache updated:', payload);
                break;
            default:
                console.log('Unknown service worker message:', type, payload);
        }
    }

    // Connectivity management

    setupConnectivityIndicators() {
        this.updateConnectivityIndicator();
        
        // Listen for connectivity changes
        this.syncManager.onConnectivityChange((isOnline) => {
            this.isOnline = isOnline;
            this.updateConnectivityIndicator();
            
            if (isOnline) {
                this.showNotification('Connection restored', 'success');
            } else {
                this.showNotification('Working offline', 'warning');
            }
        });
    }

    updateConnectivityIndicator() {
        const indicators = document.querySelectorAll('.connectivity-indicator');
        const statusElements = document.querySelectorAll('.connection-status');
        
        indicators.forEach(indicator => {
            if (this.isOnline) {
                indicator.classList.remove('offline');
                indicator.classList.add('online');
                indicator.title = 'Online';
            } else {
                indicator.classList.remove('online');
                indicator.classList.add('offline');
                indicator.title = 'Offline';
            }
        });
        
        statusElements.forEach(element => {
            element.textContent = this.isOnline ? 'Online' : 'Offline';
            element.className = `connection-status ${this.isOnline ? 'online' : 'offline'}`;
        });
    }

    // Event listeners

    setupEventListeners() {
        // Form submissions
        document.addEventListener('submit', event => {
            if (event.target.dataset.offline === 'true') {
                event.preventDefault();
                this.handleOfflineFormSubmission(event.target);
            }
        });

        // Sync buttons
        document.addEventListener('click', event => {
            if (event.target.classList.contains('sync-btn')) {
                event.preventDefault();
                this.handleSyncRequest();
            }
            
            if (event.target.classList.contains('force-sync-btn')) {
                event.preventDefault();
                this.handleForceSyncRequest();
            }
            
            if (event.target.classList.contains('install-btn')) {
                event.preventDefault();
                this.handleInstallRequest();
            }
        });

        // Task actions
        document.addEventListener('click', event => {
            if (event.target.classList.contains('task-complete-btn')) {
                event.preventDefault();
                this.handleTaskCompletion(event.target);
            }
            
            if (event.target.classList.contains('task-update-btn')) {
                event.preventDefault();
                this.handleTaskUpdate(event.target);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', event => {
            if (event.ctrlKey || event.metaKey) {
                switch (event.key) {
                    case 's':
                        event.preventDefault();
                        this.handleSyncRequest();
                        break;
                    case 'n':
                        if (event.shiftKey) {
                            event.preventDefault();
                            this.showNewTaskModal();
                        }
                        break;
                }
            }
        });
    }

    // Offline form handling

    async handleOfflineFormSubmission(form) {
        try {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            if (form.dataset.type === 'task') {
                await this.createOfflineTask(data);
                this.showNotification('Task created offline', 'success');
                
                // Redirect or update UI
                if (form.dataset.redirect) {
                    window.location.href = form.dataset.redirect;
                } else {
                    this.refreshTaskList();
                }
            }
            
        } catch (error) {
            console.error('Offline form submission failed:', error);
            this.showError('Failed to save offline');
        }
    }

    async createOfflineTask(data) {
        const task = await this.offlineDB.createOfflineTask({
            title: data.title,
            description: data.description,
            priority: data.priority || 'medium',
            task_type: data.task_type,
            vessel_id: data.vessel_id ? parseInt(data.vessel_id) : null,
            assigned_to_id: data.assigned_to_id ? parseInt(data.assigned_to_id) : null,
            due_date: data.due_date || null,
            location: data.location || '',
            equipment: data.equipment || '',
            estimated_hours: data.estimated_hours ? parseFloat(data.estimated_hours) : null
        });
        
        return task;
    }

    // Task management

    async handleTaskCompletion(button) {
        try {
            const taskId = button.dataset.taskId;
            const completionNotes = prompt('Completion notes (optional):');
            
            if (this.isOnline) {
                // Online: Submit to server
                const response = await fetch(`/api/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        status: 'completed',
                        completion_notes: completionNotes,
                        completion_date: new Date().toISOString()
                    }),
                    credentials: 'same-origin'
                });
                
                if (response.ok) {
                    this.showNotification('Task completed', 'success');
                    this.refreshTaskList();
                } else {
                    throw new Error('Failed to complete task');
                }
            } else {
                // Offline: Save locally
                await this.offlineDB.updateOfflineTask(taskId, {
                    status: 'completed',
                    completion_notes: completionNotes,
                    completion_date: new Date().toISOString()
                });
                
                this.showNotification('Task completed offline', 'success');
                this.refreshTaskList();
            }
            
        } catch (error) {
            console.error('Task completion failed:', error);
            this.showError('Failed to complete task');
        }
    }

    async handleTaskUpdate(button) {
        try {
            const taskId = button.dataset.taskId;
            const status = button.dataset.status;
            
            if (this.isOnline) {
                // Online: Submit to server
                const response = await fetch(`/api/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ status }),
                    credentials: 'same-origin'
                });
                
                if (response.ok) {
                    this.showNotification('Task updated', 'success');
                    this.refreshTaskList();
                } else {
                    throw new Error('Failed to update task');
                }
            } else {
                // Offline: Save locally
                await this.offlineDB.updateOfflineTask(taskId, { status });
                this.showNotification('Task updated offline', 'success');
                this.refreshTaskList();
            }
            
        } catch (error) {
            console.error('Task update failed:', error);
            this.showError('Failed to update task');
        }
    }

    // Sync management

    async handleSyncRequest() {
        if (!this.isOnline) {
            this.showNotification('Cannot sync while offline', 'warning');
            return;
        }

        try {
            this.showSyncProgress(true);
            await this.syncManager.triggerSync();
            await this.updateSyncStatus();
            this.showNotification('Sync completed', 'success');
        } catch (error) {
            console.error('Sync failed:', error);
            this.showError('Synchronization failed');
        } finally {
            this.showSyncProgress(false);
        }
    }

    async handleForceSyncRequest() {
        if (!this.isOnline) {
            this.showNotification('Cannot sync while offline', 'warning');
            return;
        }

        try {
            this.showSyncProgress(true);
            await this.syncManager.forceSyncAll();
            await this.updateSyncStatus();
            this.showNotification('Force sync completed', 'success');
        } catch (error) {
            console.error('Force sync failed:', error);
            this.showError('Force synchronization failed');
        } finally {
            this.showSyncProgress(false);
        }
    }

    async updateSyncStatus() {
        try {
            const stats = await this.syncManager.getSyncStatistics();
            const statusElements = document.querySelectorAll('.sync-status');
            
            statusElements.forEach(element => {
                element.innerHTML = `
                    <div class="sync-info">
                        <span class="sync-indicator ${stats.syncInProgress ? 'syncing' : 'idle'}"></span>
                        ${stats.pendingChanges} pending
                        ${stats.failedChanges > 0 ? `| ${stats.failedChanges} failed` : ''}
                    </div>
                `;
            });
            
        } catch (error) {
            console.error('Failed to update sync status:', error);
        }
    }

    showSyncProgress(show) {
        const buttons = document.querySelectorAll('.sync-btn, .force-sync-btn');
        buttons.forEach(button => {
            if (show) {
                button.disabled = true;
                button.innerHTML = '<span class="spinner"></span> Syncing...';
            } else {
                button.disabled = false;
                button.innerHTML = button.dataset.originalText || 'Sync';
            }
        });
    }

    // PWA installation

    handleInstallRequest() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            this.deferredPrompt.userChoice.then(choiceResult => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('PWA installed');
                } else {
                    console.log('PWA installation declined');
                }
                this.deferredPrompt = null;
            });
        }
    }

    // Notification management

    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission;
            console.log('Notification permission:', permission);
        }
    }

    showNotification(message, type = 'info') {
        // Show in-app notification
        this.showInAppNotification(message, type);
        
        // Show system notification if permitted and app is in background
        if (this.notificationPermission === 'granted' && document.hidden) {
            this.showSystemNotification(message, type);
        }
    }

    showInAppNotification(message, type) {
        const container = document.getElementById('notification-container') || 
                         document.body;
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    showSystemNotification(message, type) {
        if (this.notificationPermission === 'granted') {
            new Notification('Fleet Management', {
                body: message,
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-72x72.png'
            });
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showUpdateAvailable() {
        const message = 'A new version is available. Refresh to update.';
        this.showNotification(message, 'info');
    }

    // UI helpers

    refreshTaskList() {
        // Reload current page or update task list dynamically
        if (window.location.pathname.includes('/tasks') || 
            window.location.pathname.includes('/dashboard')) {
            window.location.reload();
        }
    }

    showNewTaskModal() {
        const modal = document.getElementById('new-task-modal');
        if (modal) {
            modal.style.display = 'block';
        } else {
            // Redirect to create task page
            window.location.href = '/dashboard/tasks/create';
        }
    }

    initializePage() {
        // Page-specific initialization
        const path = window.location.pathname;
        
        if (path.includes('/dashboard')) {
            this.initializeDashboard();
        } else if (path.includes('/tasks')) {
            this.initializeTasks();
        }
        
        // Update sync status
        this.updateSyncStatus();
    }

    async initializeDashboard() {
        try {
            // Load dashboard data from offline DB if available
            if (!this.isOnline) {
                await this.loadOfflineDashboardData();
            }
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
        }
    }

    async initializeTasks() {
        try {
            // Load tasks from offline DB if available
            if (!this.isOnline) {
                await this.loadOfflineTasksData();
            }
        } catch (error) {
            console.error('Tasks initialization failed:', error);
        }
    }

    async loadOfflineDashboardData() {
        // Implementation would load cached dashboard data
        console.log('Loading offline dashboard data...');
    }

    async loadOfflineTasksData() {
        // Implementation would load cached tasks data
        console.log('Loading offline tasks data...');
    }
}

// PWA installation prompt handling
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install button
    const installButtons = document.querySelectorAll('.install-btn');
    installButtons.forEach(button => {
        button.style.display = 'block';
    });
});

window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    deferredPrompt = null;
    
    // Hide install button
    const installButtons = document.querySelectorAll('.install-btn');
    installButtons.forEach(button => {
        button.style.display = 'none';
    });
});

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.fleetApp = new FleetApp();
});

// Export for global access
window.FleetApp = FleetApp;