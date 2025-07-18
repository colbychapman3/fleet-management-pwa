/**
 * Vessel Operations Background Sync
 * Handles offline submission sync and background data synchronization
 */

class VesselSyncManager {
    constructor(offlineDB, options = {}) {
        this.offlineDB = offlineDB;
        this.options = {
            syncInterval: 60000, // 1 minute
            maxRetries: 3,
            retryDelay: 5000, // 5 seconds
            batchSize: 10,
            ...options
        };
        
        this.syncInProgress = false;
        this.syncTimer = null;
        this.lastSyncTime = null;
        this.syncCallbacks = new Set();
        
        this.init();
    }

    init() {
        // Listen for online/offline events
        window.addEventListener('online', () => {
            console.log('Back online - triggering sync');
            this.triggerSync();
        });

        // Start periodic sync when online
        if (navigator.onLine) {
            this.startPeriodicSync();
        }

        // Listen for visibility changes to sync when app becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && navigator.onLine) {
                this.triggerSync();
            }
        });

        console.log('Vessel Sync Manager initialized');
    }

    // Sync management
    startPeriodicSync() {
        if (this.syncTimer) {
            clearInterval(this.syncTimer);
        }

        this.syncTimer = setInterval(() => {
            if (navigator.onLine && !this.syncInProgress) {
                this.triggerSync();
            }
        }, this.options.syncInterval);

        console.log(`Periodic sync started (interval: ${this.options.syncInterval}ms)`);
    }

    stopPeriodicSync() {
        if (this.syncTimer) {
            clearInterval(this.syncTimer);
            this.syncTimer = null;
        }
        console.log('Periodic sync stopped');
    }

    onSyncComplete(callback) {
        this.syncCallbacks.add(callback);
    }

    offSyncComplete(callback) {
        this.syncCallbacks.delete(callback);
    }

    // Main sync orchestration
    async triggerSync() {
        if (this.syncInProgress || !navigator.onLine) {
            return false;
        }

        this.syncInProgress = true;
        const startTime = Date.now();

        try {
            console.log('Starting vessel operations sync...');

            // Sync in priority order
            const results = {
                submissions: await this.syncOfflineSubmissions(),
                wizardData: await this.syncWizardAutoSaves(),
                maritime: await this.syncMaritimeData(),
                general: await this.syncGeneralQueue()
            };

            this.lastSyncTime = new Date().toISOString();
            const duration = Date.now() - startTime;

            console.log(`Sync completed in ${duration}ms:`, results);

            // Notify callbacks
            this.syncCallbacks.forEach(callback => {
                try {
                    callback({ success: true, results, duration });
                } catch (error) {
                    console.error('Sync callback error:', error);
                }
            });

            return results;

        } catch (error) {
            console.error('Sync failed:', error);
            
            this.syncCallbacks.forEach(callback => {
                try {
                    callback({ success: false, error: error.message });
                } catch (callbackError) {
                    console.error('Sync callback error:', callbackError);
                }
            });

            throw error;

        } finally {
            this.syncInProgress = false;
        }
    }

    // Sync offline submissions
    async syncOfflineSubmissions() {
        const submissions = await this.offlineDB.getPendingSubmissions();
        const results = {
            processed: 0,
            succeeded: 0,
            failed: 0,
            errors: []
        };

        console.log(`Syncing ${submissions.length} offline submissions...`);

        for (const submission of submissions.slice(0, this.options.batchSize)) {
            results.processed++;

            try {
                if (submission.retry_count >= this.options.maxRetries) {
                    console.warn(`Submission ${submission.id} exceeded max retries`);
                    await this.offlineDB.updateSubmissionStatus(
                        submission.id, 
                        'failed', 
                        'Exceeded maximum retry attempts'
                    );
                    results.failed++;
                    continue;
                }

                await this.syncSingleSubmission(submission);
                await this.offlineDB.updateSubmissionStatus(submission.id, 'completed');
                results.succeeded++;

            } catch (error) {
                console.error(`Failed to sync submission ${submission.id}:`, error);
                await this.offlineDB.updateSubmissionStatus(
                    submission.id, 
                    'failed', 
                    error.message
                );
                results.failed++;
                results.errors.push({
                    submissionId: submission.id,
                    error: error.message
                });
            }
        }

        return results;
    }

    async syncSingleSubmission(submission) {
        const { type, data } = submission;

        switch (type) {
            case 'vessel-operations':
                return this.syncVesselOperation(data);
            case 'ship-operation':
                return this.syncShipOperation(data);
            default:
                throw new Error(`Unknown submission type: ${type}`);
        }
    }

    async syncVesselOperation(data) {
        const response = await fetch('/api/maritime/ship-operations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    async syncShipOperation(data) {
        const response = await fetch('/api/maritime/ship-operations', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    // Sync wizard auto-save data
    async syncWizardAutoSaves() {
        const wizardData = await this.offlineDB.getAllWizardData();
        const results = {
            processed: wizardData.length,
            backed_up: 0
        };

        // For now, wizard data is kept locally for resumption
        // In the future, this could sync partial data to server for backup
        console.log(`Found ${wizardData.length} saved wizard sessions`);

        // Optional: Backup wizard progress to server for cross-device sync
        for (const wizard of wizardData) {
            try {
                await this.backupWizardProgress(wizard);
                results.backed_up++;
            } catch (error) {
                console.warn(`Failed to backup wizard ${wizard.wizard_type}:`, error);
            }
        }

        return results;
    }

    async backupWizardProgress(wizardData) {
        // Optional API call to backup wizard progress
        const response = await fetch('/api/wizard/backup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                wizard_type: wizardData.wizard_type,
                step: wizardData.last_step,
                timestamp: wizardData.timestamp,
                checksum: this.generateDataChecksum(wizardData.data)
            }),
            credentials: 'same-origin'
        });

        if (response.ok) {
            return response.json();
        }
        // Non-critical, so don't throw errors
        return null;
    }

    // Sync maritime reference data
    async syncMaritimeData() {
        const results = {
            berths: await this.syncBerthData(),
            teams: await this.syncTeamData(),
            zones: await this.syncZoneData()
        };

        return results;
    }

    async syncBerthData() {
        try {
            const response = await fetch('/api/maritime/berths', {
                credentials: 'same-origin'
            });

            if (response.ok) {
                const berthData = await response.json();
                await this.offlineDB.saveBerthData(berthData);
                return { success: true, count: berthData.length };
            }
        } catch (error) {
            console.warn('Failed to sync berth data:', error);
        }

        return { success: false };
    }

    async syncTeamData() {
        try {
            const response = await fetch('/api/maritime/teams', {
                credentials: 'same-origin'
            });

            if (response.ok) {
                const teamData = await response.json();
                await this.offlineDB.saveTeamData(teamData);
                return { success: true, count: teamData.length };
            }
        } catch (error) {
            console.warn('Failed to sync team data:', error);
        }

        return { success: false };
    }

    async syncZoneData() {
        try {
            const response = await fetch('/api/maritime/cargo-zones', {
                credentials: 'same-origin'
            });

            if (response.ok) {
                const zoneData = await response.json();
                await this.offlineDB.saveCargoZoneData(zoneData);
                return { success: true, count: zoneData.length };
            }
        } catch (error) {
            console.warn('Failed to sync zone data:', error);
        }

        return { success: false };
    }

    // Sync general data (tasks, users, etc.)
    async syncGeneralQueue() {
        const syncQueue = await this.offlineDB.getSyncQueue();
        const results = {
            processed: 0,
            succeeded: 0,
            failed: 0
        };

        for (const item of syncQueue.slice(0, this.options.batchSize)) {
            results.processed++;

            try {
                await this.syncQueueItem(item);
                await this.offlineDB.removeSyncItem(item.id);
                results.succeeded++;
            } catch (error) {
                console.error(`Failed to sync queue item ${item.id}:`, error);
                results.failed++;
            }
        }

        return results;
    }

    async syncQueueItem(item) {
        const { table, action, data } = item;

        const endpoint = this.getApiEndpoint(table);
        let method, url;

        switch (action) {
            case 'create':
                method = 'POST';
                url = endpoint;
                break;
            case 'update':
                method = 'PUT';
                url = `${endpoint}/${data.id}`;
                break;
            case 'delete':
                method = 'DELETE';
                url = `${endpoint}/${data.id}`;
                break;
            default:
                throw new Error(`Unknown action: ${action}`);
        }

        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: action !== 'delete' ? JSON.stringify(data) : undefined,
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    getApiEndpoint(table) {
        const endpoints = {
            tasks: '/api/tasks',
            users: '/api/users',
            vessels: '/api/vessels',
            ship_operations: '/api/maritime/ship-operations'
        };

        return endpoints[table] || `/api/${table}`;
    }

    // Utility methods
    generateDataChecksum(data) {
        // Simple checksum for data integrity
        const str = JSON.stringify(data);
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return hash.toString(16);
    }

    // Force sync with retry
    async forceSyncAll() {
        let retryCount = 0;
        
        while (retryCount < this.options.maxRetries) {
            try {
                return await this.triggerSync();
            } catch (error) {
                retryCount++;
                console.warn(`Force sync attempt ${retryCount} failed:`, error);
                
                if (retryCount < this.options.maxRetries) {
                    await this.delay(this.options.retryDelay * retryCount);
                } else {
                    throw error;
                }
            }
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Statistics and monitoring
    async getSyncStatistics() {
        const [
            pendingSubmissions,
            syncQueue,
            maritimeStats
        ] = await Promise.all([
            this.offlineDB.getPendingSubmissions(),
            this.offlineDB.getSyncQueue(),
            this.offlineDB.getMaritimeStats()
        ]);

        return {
            syncInProgress: this.syncInProgress,
            lastSyncTime: this.lastSyncTime,
            pendingChanges: pendingSubmissions.length + syncQueue.length,
            failedChanges: pendingSubmissions.filter(s => s.status === 'failed').length,
            maritime: maritimeStats,
            isOnline: navigator.onLine
        };
    }

    // Cleanup methods
    async performMaintenance() {
        console.log('Performing sync maintenance...');
        
        const results = {
            clearedExpiredCache: 0,
            clearedOldWizards: 0,
            clearedCompletedSubmissions: 0
        };

        try {
            // Clear expired cache
            await this.offlineDB.clearExpiredCache();
            
            // Clear old wizard data (older than 7 days)
            results.clearedOldWizards = await this.offlineDB.cleanupOldWizardData(7);
            
            // Clear completed submissions (older than 30 days)
            results.clearedCompletedSubmissions = await this.offlineDB.cleanupCompletedSubmissions(30);
            
            console.log('Maintenance completed:', results);
            
        } catch (error) {
            console.error('Maintenance failed:', error);
        }

        return results;
    }

    // Destroy
    destroy() {
        this.stopPeriodicSync();
        this.syncCallbacks.clear();
        
        window.removeEventListener('online', this.triggerSync);
        document.removeEventListener('visibilitychange', this.triggerSync);
        
        console.log('Vessel Sync Manager destroyed');
    }
}

// Export for global access
window.VesselSyncManager = VesselSyncManager;