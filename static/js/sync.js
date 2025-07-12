/**
 * Synchronization manager for offline/online data sync
 * Handles background sync, conflict resolution, and connectivity monitoring
 */

class SyncManager {
    constructor(offlineDB) {
        this.offlineDB = offlineDB;
        this.isOnline = navigator.onLine;
        this.syncInProgress = false;
        this.syncCallbacks = [];
        this.retryDelay = 5000; // 5 seconds
        this.maxRetries = 3;
        
        this.init();
    }

    init() {
        // Listen for online/offline events
        window.addEventListener('online', () => {
            console.log('Connection restored');
            this.isOnline = true;
            this.triggerSync();
            this.notifyConnectivityChange(true);
        });

        window.addEventListener('offline', () => {
            console.log('Connection lost');
            this.isOnline = false;
            this.syncInProgress = false;
            this.notifyConnectivityChange(false);
        });

        // Periodic sync when online
        setInterval(() => {
            if (this.isOnline && !this.syncInProgress) {
                this.backgroundSync();
            }
        }, 30000); // Every 30 seconds

        // Initial sync if online
        if (this.isOnline) {
            setTimeout(() => this.triggerSync(), 1000);
        }
    }

    // Connectivity management

    onConnectivityChange(callback) {
        this.syncCallbacks.push(callback);
    }

    notifyConnectivityChange(isOnline) {
        this.syncCallbacks.forEach(callback => {
            try {
                callback(isOnline);
            } catch (error) {
                console.error('Sync callback error:', error);
            }
        });
    }

    async checkConnectivity() {
        if (!navigator.onLine) {
            return false;
        }

        try {
            const response = await fetch('/health', {
                method: 'HEAD',
                cache: 'no-cache'
            });
            return response.ok;
        } catch (error) {
            console.warn('Connectivity check failed:', error);
            return false;
        }
    }

    // Sync operations

    async triggerSync() {
        if (this.syncInProgress) {
            console.log('Sync already in progress');
            return;
        }

        this.syncInProgress = true;
        
        try {
            console.log('Starting data synchronization...');
            
            // Check actual connectivity
            const isConnected = await this.checkConnectivity();
            if (!isConnected) {
                console.log('No network connectivity available');
                this.isOnline = false;
                return;
            }

            // Sync pending changes first
            await this.syncPendingChanges();
            
            // Then download fresh data
            await this.downloadFreshData();
            
            console.log('Synchronization completed successfully');
            
        } catch (error) {
            console.error('Synchronization failed:', error);
            throw error;
        } finally {
            this.syncInProgress = false;
        }
    }

    async backgroundSync() {
        try {
            // Light background sync - only pending changes
            await this.syncPendingChanges();
        } catch (error) {
            console.error('Background sync failed:', error);
        }
    }

    async syncPendingChanges() {
        const pendingChanges = await this.offlineDB.getSyncQueue();
        
        if (pendingChanges.length === 0) {
            console.log('No pending changes to sync');
            return;
        }

        console.log(`Syncing ${pendingChanges.length} pending changes...`);

        for (const change of pendingChanges) {
            try {
                await this.syncSingleChange(change);
                await this.offlineDB.removeSyncItem(change.id);
            } catch (error) {
                console.error('Failed to sync change:', change.id, error);
                
                // Increment retry count
                change.retry_count = (change.retry_count || 0) + 1;
                
                if (change.retry_count >= this.maxRetries) {
                    console.error('Max retries reached for change:', change.id);
                    // Keep in queue but mark as failed
                    change.status = 'failed';
                    await this.offlineDB.put('sync_queue', change);
                } else {
                    // Update retry count
                    await this.offlineDB.put('sync_queue', change);
                }
            }
        }
    }

    async syncSingleChange(change) {
        const { table, action, data } = change;
        
        console.log(`Syncing ${action} on ${table}:`, data.id || data.local_id);

        const response = await fetch('/api/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                changes: [change]
            }),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(`Sync failed: ${response.status} - ${errorData.error || response.statusText}`);
        }

        const result = await response.json();
        
        // Handle sync result
        if (result.results && result.results[0]) {
            const syncResult = result.results[0].result;
            
            if (syncResult.status === 'created' && syncResult.server_id) {
                // Update local record with server ID
                await this.updateLocalRecordWithServerId(table, data, syncResult.server_id);
            }
        }

        return result;
    }

    async updateLocalRecordWithServerId(table, localData, serverId) {
        if (table === 'tasks') {
            const updatedTask = {
                ...localData,
                id: serverId,
                is_synced: true,
                offline_created: false
            };
            
            // Remove old local record
            if (localData.id && localData.id.toString().startsWith('local_')) {
                await this.offlineDB.delete('tasks', localData.id);
            }
            
            // Add with server ID
            await this.offlineDB.put('tasks', updatedTask);
        }
    }

    async downloadFreshData() {
        console.log('Downloading fresh data from server...');

        try {
            // Download tasks
            await this.downloadTasks();
            
            // Download users (if manager)
            await this.downloadUsers();
            
            // Download vessels
            await this.downloadVessels();
            
            console.log('Fresh data downloaded successfully');
            
        } catch (error) {
            console.error('Failed to download fresh data:', error);
            throw error;
        }
    }

    async downloadTasks() {
        try {
            const response = await fetch('/api/tasks?per_page=100', {
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to download tasks: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.tasks && Array.isArray(data.tasks)) {
                await this.offlineDB.bulkImportTasks(data.tasks);
                console.log(`Downloaded ${data.tasks.length} tasks`);
            }
            
        } catch (error) {
            console.error('Task download failed:', error);
            throw error;
        }
    }

    async downloadUsers() {
        try {
            const response = await fetch('/api/users', {
                credentials: 'same-origin'
            });
            
            if (response.status === 403) {
                console.log('No access to users data (worker role)');
                return;
            }
            
            if (!response.ok) {
                throw new Error(`Failed to download users: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.users && Array.isArray(data.users)) {
                await this.offlineDB.bulkImportUsers(data.users);
                console.log(`Downloaded ${data.users.length} users`);
            }
            
        } catch (error) {
            console.error('Users download failed:', error);
            // Don't throw - users may not be accessible for workers
        }
    }

    async downloadVessels() {
        try {
            const response = await fetch('/api/vessels', {
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to download vessels: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.vessels && Array.isArray(data.vessels)) {
                await this.offlineDB.bulkImportVessels(data.vessels);
                console.log(`Downloaded ${data.vessels.length} vessels`);
            }
            
        } catch (error) {
            console.error('Vessels download failed:', error);
            throw error;
        }
    }

    // Manual sync triggers

    async forceSyncTask(taskId) {
        try {
            const task = await this.offlineDB.get('tasks', taskId);
            if (!task) {
                throw new Error('Task not found');
            }

            if (!task.is_synced) {
                await this.offlineDB.queueSync('tasks', 'update', task);
            }

            if (this.isOnline) {
                await this.syncPendingChanges();
            }

            return task;
        } catch (error) {
            console.error('Force sync task failed:', error);
            throw error;
        }
    }

    async forceSyncAll() {
        if (!this.isOnline) {
            throw new Error('Cannot sync while offline');
        }

        return this.triggerSync();
    }

    // Conflict resolution

    async resolveConflict(localData, serverData) {
        // Simple last-write-wins strategy
        // In production, you might want more sophisticated conflict resolution
        
        const localTime = new Date(localData.updated_at);
        const serverTime = new Date(serverData.updated_at);
        
        if (localTime > serverTime) {
            console.log('Local version is newer, keeping local changes');
            return localData;
        } else {
            console.log('Server version is newer, accepting server changes');
            return serverData;
        }
    }

    // Status and monitoring

    getSyncStatus() {
        return {
            isOnline: this.isOnline,
            syncInProgress: this.syncInProgress,
            lastSync: this.lastSyncTime,
            pendingChanges: 0 // Will be updated by caller
        };
    }

    async getSyncStatistics() {
        const pendingChanges = await this.offlineDB.getSyncQueue();
        const pendingCount = pendingChanges.length;
        const failedCount = pendingChanges.filter(c => c.status === 'failed').length;
        
        return {
            isOnline: this.isOnline,
            syncInProgress: this.syncInProgress,
            pendingChanges: pendingCount,
            failedChanges: failedCount,
            lastSync: this.lastSyncTime
        };
    }

    // Service Worker integration

    registerBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then(registration => {
                return registration.sync.register('task-sync');
            }).then(() => {
                console.log('Background sync registered');
            }).catch(error => {
                console.error('Background sync registration failed:', error);
            });
        }
    }

    // Utility methods

    async clearFailedSyncs() {
        const pendingChanges = await this.offlineDB.getSyncQueue();
        const failedChanges = pendingChanges.filter(c => c.status === 'failed');
        
        for (const change of failedChanges) {
            await this.offlineDB.removeSyncItem(change.id);
        }
        
        console.log(`Cleared ${failedChanges.length} failed sync items`);
        return failedChanges.length;
    }

    async retryFailedSyncs() {
        if (!this.isOnline) {
            throw new Error('Cannot retry while offline');
        }

        const pendingChanges = await this.offlineDB.getSyncQueue();
        const failedChanges = pendingChanges.filter(c => c.status === 'failed');
        
        console.log(`Retrying ${failedChanges.length} failed syncs...`);
        
        for (const change of failedChanges) {
            change.status = 'pending';
            change.retry_count = 0;
            await this.offlineDB.put('sync_queue', change);
        }
        
        await this.syncPendingChanges();
        return failedChanges.length;
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SyncManager;
}

// Global instance for non-module usage
window.SyncManager = SyncManager;