/**
 * IndexedDB wrapper for offline data storage and synchronization
 * Handles local storage of tasks, users, vessels, and sync queue
 */

class OfflineDB {
    constructor() {
        this.dbName = 'FleetOfflineDB';
        this.version = 1;
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => {
                console.error('Failed to open IndexedDB:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                console.log('IndexedDB opened successfully');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                this.createStores(db);
            };
        });
    }

    createStores(db) {
        console.log('Creating IndexedDB object stores...');

        // Tasks store
        if (!db.objectStoreNames.contains('tasks')) {
            const tasksStore = db.createObjectStore('tasks', { keyPath: 'id' });
            tasksStore.createIndex('status', 'status', { unique: false });
            tasksStore.createIndex('assigned_to_id', 'assigned_to_id', { unique: false });
            tasksStore.createIndex('vessel_id', 'vessel_id', { unique: false });
            tasksStore.createIndex('due_date', 'due_date', { unique: false });
            tasksStore.createIndex('local_id', 'local_id', { unique: true });
        }

        // Users store
        if (!db.objectStoreNames.contains('users')) {
            const usersStore = db.createObjectStore('users', { keyPath: 'id' });
            usersStore.createIndex('email', 'email', { unique: true });
            usersStore.createIndex('role', 'role', { unique: false });
            usersStore.createIndex('vessel_id', 'vessel_id', { unique: false });
        }

        // Vessels store
        if (!db.objectStoreNames.contains('vessels')) {
            const vesselsStore = db.createObjectStore('vessels', { keyPath: 'id' });
            ves­selsStore.createIndex('name', 'name', { unique: false });
            vesselsStore.createIndex('status', 'status', { unique: false });
        }

        // Sync queue store
        if (!db.objectStoreNames.contains('sync_queue')) {
            const syncStore = db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
            syncStore.createIndex('table', 'table', { unique: false });
            syncStore.createIndex('action', 'action', { unique: false });
            syncStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Cached data store for API responses
        if (!db.objectStoreNames.contains('cached_data')) {
            const cacheStore = db.createObjectStore('cached_data', { keyPath: 'key' });
            cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // App settings store
        if (!db.objectStoreNames.contains('settings')) {
            db.createObjectStore('settings', { keyPath: 'key' });
        }

        console.log('IndexedDB object stores created successfully');
    }

    // Generic CRUD operations

    async add(storeName, data) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(data);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async put(storeName, data) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.put(data);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async get(storeName, key) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(key);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async getAll(storeName) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.getAll();

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async delete(storeName, key) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(key);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async clear(storeName) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.clear();

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    // Task-specific operations

    async getAllTasks() {
        return this.getAll('tasks');
    }

    async getTasksByStatus(status) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['tasks'], 'readonly');
            const store = transaction.objectStore('tasks');
            const index = store.index('status');
            const request = index.getAll(status);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async getTasksByUser(userId) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['tasks'], 'readonly');
            const store = transaction.objectStore('tasks');
            const index = store.index('assigned_to_id');
            const request = index.getAll(userId);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async getTasksByVessel(vesselId) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['tasks'], 'readonly');
            const store = transaction.objectStore('tasks');
            const index = store.index('vessel_id');
            const request = index.getAll(vesselId);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async saveTask(task) {
        // Add timestamp for offline tracking
        task.offline_updated = new Date().toISOString();
        task.is_synced = false;
        
        return this.put('tasks', task);
    }

    async createOfflineTask(taskData) {
        // Generate local ID for offline-created tasks
        const localId = this.generateUUID();
        const task = {
            ...taskData,
            local_id: localId,
            id: `local_${localId}`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            is_synced: false,
            offline_created: true
        };

        await this.saveTask(task);
        await this.queueSync('tasks', 'create', task);
        
        return task;
    }

    async updateOfflineTask(taskId, updates) {
        const existingTask = await this.get('tasks', taskId);
        if (!existingTask) {
            throw new Error('Task not found');
        }

        const updatedTask = {
            ...existingTask,
            ...updates,
            updated_at: new Date().toISOString(),
            is_synced: false
        };

        await this.saveTask(updatedTask);
        await this.queueSync('tasks', 'update', updatedTask);
        
        return updatedTask;
    }

    // Sync queue operations

    async queueSync(table, action, data) {
        const syncItem = {
            table,
            action,
            data,
            timestamp: new Date().toISOString(),
            retry_count: 0,
            local_id: data.local_id || null,
            server_id: data.id && !data.id.toString().startsWith('local_') ? data.id : null
        };

        return this.add('sync_queue', syncItem);
    }

    async getSyncQueue() {
        return this.getAll('sync_queue');
    }

    async removeSyncItem(id) {
        return this.delete('sync_queue', id);
    }

    async clearSyncQueue() {
        return this.clear('sync_queue');
    }

    // Cache operations

    async cacheData(key, data, ttl = 300000) { // 5 minutes default TTL
        const cacheItem = {
            key,
            data,
            timestamp: Date.now(),
            ttl,
            expires: Date.now() + ttl
        };

        return this.put('cached_data', cacheItem);
    }

    async getCachedData(key) {
        const item = await this.get('cached_data', key);
        
        if (!item) return null;
        
        // Check if expired
        if (Date.now() > item.expires) {
            await this.delete('cached_data', key);
            return null;
        }
        
        return item.data;
    }

    async clearExpiredCache() {
        const allCached = await this.getAll('cached_data');
        const now = Date.now();
        
        for (const item of allCached) {
            if (now > item.expires) {
                await this.delete('cached_data', item.key);
            }
        }
    }

    // Settings operations

    async getSetting(key, defaultValue = null) {
        const setting = await this.get('settings', key);
        return setting ? setting.value : defaultValue;
    }

    async setSetting(key, value) {
        return this.put('settings', { key, value });
    }

    // Bulk operations for data synchronization

    async bulkImportTasks(tasks) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['tasks'], 'readwrite');
            const store = transaction.objectStore('tasks');
            
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
            
            tasks.forEach(task => {
                task.is_synced = true;
                store.put(task);
            });
        });
    }

    async bulkImportUsers(users) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['users'], 'readwrite');
            const store = transaction.objectStore('users');
            
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
            
            users.forEach(user => {
                store.put(user);
            });
        });
    }

    async bulkImportVessels(vessels) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['vessels'], 'readwrite');
            const store = transaction.objectStore('vessels');
            
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
            
            vessels.forEach(vessel => {
                store.put(vessel);
            });
        });
    }

    // Utility functions

    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    async getStorageStats() {
        const stats = {};
        const storeNames = ['tasks', 'users', 'vessels', 'sync_queue', 'cached_data', 'settings'];
        
        for (const storeName of storeNames) {
            try {
                const items = await this.getAll(storeName);
                stats[storeName] = items.length;
            } catch (error) {
                stats[storeName] = 0;
            }
        }
        
        return stats;
    }

    async exportData() {
        const data = {};
        const storeNames = ['tasks', 'users', 'vessels', 'settings'];
        
        for (const storeName of storeNames) {
            try {
                data[storeName] = await this.getAll(storeName);
            } catch (error) {
                console.error(`Failed to export ${storeName}:`, error);
                data[storeName] = [];
            }
        }
        
        return data;
    }

    async importData(data) {
        for (const [storeName, items] of Object.entries(data)) {
            if (Array.isArray(items)) {
                try {
                    await this.clear(storeName);
                    for (const item of items) {
                        await this.put(storeName, item);
                    }
                } catch (error) {
                    console.error(`Failed to import ${storeName}:`, error);
                }
            }
        }
    }

    // Health check
    async healthCheck() {
        try {
            if (!this.db) await this.init();
            
            const stats = await this.getStorageStats();
            return {
                status: 'healthy',
                database: this.dbName,
                version: this.version,
                stores: stats,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                status: 'error',
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OfflineDB;
}

// Global instance for non-module usage
window.offlineDB = new OfflineDB();