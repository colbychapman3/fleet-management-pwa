/**
 * Operations Dashboard JavaScript
 * Real-time multi-ship operations management
 */

class OperationsDashboard {
    constructor() {
        this.wsConnection = null;
        this.updateInterval = null;
        this.lastUpdateTime = null;
        this.isOnline = navigator.onLine;
        this.pendingUpdates = [];
        
        this.init();
        this.setupEventListeners();
        this.setupWebSocket();
        this.setupOfflineSync();
    }
    
    init() {
        console.log('Initializing Operations Dashboard');
        this.startPeriodicUpdates();
        this.setupDragAndDrop();
        this.updateConnectionStatus();
    }
    
    setupEventListeners() {
        // Online/offline detection
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateConnectionStatus();
            this.syncPendingUpdates();
            this.setupWebSocket();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateConnectionStatus();
            if (this.wsConnection) {
                this.wsConnection.close();
            }
        });
        
        // Visibility change (tab switch)
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.refreshDashboard();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshDashboard();
                        break;
                    case 'n':
                        e.preventDefault();
                        this.initializeOperation();
                        break;
                }
            }
        });
    }
    
    setupWebSocket() {
        if (!this.isOnline) return;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/operations`;
        
        try {
            this.wsConnection = new WebSocket(wsUrl);
            
            this.wsConnection.onopen = () => {
                console.log('WebSocket connected');
                this.updateRealTimeStatus(true);
            };
            
            this.wsConnection.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleRealTimeUpdate(data);
            };
            
            this.wsConnection.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateRealTimeStatus(false);
                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    if (this.isOnline) {
                        this.setupWebSocket();
                    }
                }, 5000);
            };
            
            this.wsConnection.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateRealTimeStatus(false);
            };
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }
    
    setupOfflineSync() {
        // Register service worker for offline sync
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.ready.then(registration => {
                if ('sync' in window.ServiceWorkerRegistration.prototype) {
                    // Background sync is available
                    console.log('Background sync available');
                }
            });
        }
    }
    
    setupDragAndDrop() {
        // Make vessel queue items draggable
        const queueItems = document.querySelectorAll('.queue-item');
        const berths = document.querySelectorAll('.berth');
        
        queueItems.forEach(item => {
            item.draggable = true;
            
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', item.dataset.vesselId);
                item.classList.add('dragging');
            });
            
            item.addEventListener('dragend', () => {
                item.classList.remove('dragging');
            });
        });
        
        berths.forEach(berth => {
            berth.addEventListener('dragover', (e) => {
                e.preventDefault();
                berth.classList.add('drag-over');
            });
            
            berth.addEventListener('dragleave', () => {
                berth.classList.remove('drag-over');
            });
            
            berth.addEventListener('drop', (e) => {
                e.preventDefault();
                berth.classList.remove('drag-over');
                
                const vesselId = e.dataTransfer.getData('text/plain');
                const berthNumber = berth.id.split('-')[1];
                
                this.assignVesselToBerth(vesselId, berthNumber);
            });
        });
    }
    
    startPeriodicUpdates() {
        // Update dashboard every 30 seconds when online
        this.updateInterval = setInterval(() => {
            if (this.isOnline && document.visibilityState === 'visible') {
                this.refreshDashboardData();
            }
        }, 30000);
    }
    
    handleRealTimeUpdate(data) {
        console.log('Real-time update received:', data);
        
        switch (data.type) {
            case 'operation_update':
                this.updateOperationCard(data.operation);
                break;
            case 'berth_status_change':
                this.updateBerthStatus(data.berth, data.status);
                break;
            case 'kpi_update':
                this.updateKPIs(data.kpis);
                break;
            case 'alert':
                this.addAlert(data.alert);
                break;
            case 'team_status_change':
                this.updateTeamStatus(data.team);
                break;
            default:
                console.log('Unknown update type:', data.type);
        }
        
        this.lastUpdateTime = new Date();
        this.updateLastUpdateTime();
    }
    
    updateOperationCard(operation) {
        const card = document.querySelector(`[data-operation-id="${operation.id}"]`);
        if (!card) return;
        
        // Update progress
        const progressFill = card.querySelector('.progress-fill');
        const progressText = card.querySelector('.progress-text');
        if (progressFill && progressText) {
            progressFill.style.width = `${operation.progress_percentage}%`;
            progressText.textContent = `${operation.progress_percentage}%`;
        }
        
        // Update step indicators
        this.updateStepIndicators(card, operation);
        
        // Update status badge
        const statusBadge = card.querySelector('.status-badge');
        if (statusBadge) {
            statusBadge.textContent = operation.status.replace('_', ' ').toUpperCase();
            statusBadge.className = `status-badge status-${operation.status}`;
        }
        
        // Add animation to show update
        card.classList.add('animate-fade-in');
        setTimeout(() => card.classList.remove('animate-fade-in'), 300);
    }
    
    updateStepIndicators(card, operation) {
        const indicators = card.querySelectorAll('.step-indicator');
        
        indicators.forEach((indicator, index) => {
            const stepNumber = index + 1;
            indicator.classList.remove('completed', 'active', 'pending');
            
            if (operation[`step_${stepNumber}_completed`]) {
                indicator.classList.add('completed');
            } else if (operation.current_step === stepNumber) {
                indicator.classList.add('active');
            } else {
                indicator.classList.add('pending');
            }
        });
    }
    
    updateBerthStatus(berthData, status) {
        const berth = document.querySelector(`#berth-${berthData.number}`);
        if (!berth) return;
        
        // Remove all status classes
        berth.classList.remove('berth-occupied', 'berth-maintenance', 'berth-reserved');
        
        // Add new status class
        berth.classList.add(`berth-${status}`);
        
        // Update content based on status
        if (status === 'occupied' && berthData.vessel) {
            this.renderBerthVesselInfo(berth, berthData.vessel);
        } else if (status === 'available') {
            this.renderEmptyBerth(berth);
        }
    }
    
    updateKPIs(kpis) {
        Object.keys(kpis).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.textContent = kpis[key];
                
                // Add flash animation for significant changes
                element.classList.add('animate-fade-in');
                setTimeout(() => element.classList.remove('animate-fade-in'), 300);
            }
        });
    }
    
    addAlert(alert) {
        const alertsList = document.getElementById('alerts-list');
        if (!alertsList) return;
        
        const alertElement = this.createAlertElement(alert);
        alertsList.insertBefore(alertElement, alertsList.firstChild);
        
        // Auto-remove info alerts after 10 seconds
        if (alert.severity === 'info') {
            setTimeout(() => {
                if (alertElement.parentNode) {
                    alertElement.remove();
                }
            }, 10000);
        }
        
        // Show notification
        this.showNotification(alert.title, alert.message, alert.severity);
    }
    
    createAlertElement(alert) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert-item alert-${alert.severity}`;
        alertDiv.dataset.alertId = alert.id;
        
        alertDiv.innerHTML = `
            <div class="alert-icon">
                <i class="icon-${alert.icon}"></i>
            </div>
            <div class="alert-content">
                <div class="alert-title">${alert.title}</div>
                <div class="alert-message">${alert.message}</div>
                <div class="alert-time">${new Date(alert.created_at).toLocaleTimeString()}</div>
            </div>
            <div class="alert-actions">
                <button class="btn btn-sm btn-outline" onclick="operationsDashboard.dismissAlert('${alert.id}')">
                    <i class="icon-x"></i>
                </button>
            </div>
        `;
        
        return alertDiv;
    }
    
    updateTeamStatus(team) {
        const teamCard = document.querySelector(`[data-team-id="${team.id}"]`);
        if (!teamCard) return;
        
        // Update status badge
        const statusBadge = teamCard.querySelector('.team-status');
        if (statusBadge) {
            statusBadge.textContent = team.status.replace('_', ' ').toUpperCase();
            statusBadge.className = `team-status status-${team.status}`;
        }
        
        // Update stats
        const stats = teamCard.querySelectorAll('.stat-value');
        if (stats.length >= 3) {
            stats[0].textContent = team.cargo_processed_today;
            stats[1].textContent = `${team.efficiency_rating}%`;
            stats[2].textContent = team.active_members_count;
        }
    }
    
    updateConnectionStatus() {
        const connectivityBar = document.querySelector('.connectivity-bar');
        const indicator = document.querySelector('.connectivity-indicator');
        const statusText = document.querySelector('.connection-status');
        
        if (this.isOnline) {
            connectivityBar?.classList.remove('offline');
            indicator?.classList.remove('offline');
            if (statusText) statusText.textContent = 'Online';
        } else {
            connectivityBar?.classList.add('offline');
            indicator?.classList.add('offline');
            if (statusText) statusText.textContent = 'Offline - Working with cached data';
        }
    }
    
    updateRealTimeStatus(connected) {
        const indicators = document.querySelectorAll('.real-time-indicator');
        indicators.forEach(indicator => {
            if (connected) {
                indicator.classList.remove('disconnected');
                indicator.querySelector('.real-time-text')?.textContent = 'Live';
            } else {
                indicator.classList.add('disconnected');
                indicator.querySelector('.real-time-text')?.textContent = 'Disconnected';
            }
        });
    }
    
    updateLastUpdateTime() {
        const timeElements = document.querySelectorAll('.last-update-time');
        const timeStr = this.lastUpdateTime ? 
            this.lastUpdateTime.toLocaleTimeString() : 'Never';
        
        timeElements.forEach(el => {
            el.textContent = timeStr;
        });
    }
    
    // API Methods
    async refreshDashboard() {
        console.log('Refreshing dashboard...');
        this.showLoading('Refreshing dashboard...');
        
        try {
            if (this.isOnline) {
                await this.refreshDashboardData();
                this.showNotification('Dashboard Updated', 'Latest data loaded successfully', 'success');
            } else {
                this.loadCachedData();
                this.showNotification('Offline Mode', 'Showing cached data', 'info');
            }
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
            this.showNotification('Update Failed', 'Could not refresh dashboard data', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async refreshDashboardData() {
        const endpoints = [
            '/api/maritime/operations/active',
            '/api/maritime/berths/status',
            '/api/maritime/teams/performance',
            '/api/maritime/kpis',
            '/api/maritime/alerts/active'
        ];
        
        const responses = await Promise.all(
            endpoints.map(endpoint => 
                fetch(endpoint).then(r => r.ok ? r.json() : null)
            )
        );
        
        const [operations, berths, teams, kpis, alerts] = responses;
        
        if (operations) this.updateOperationsList(operations);
        if (berths) this.updateBerthsDisplay(berths);
        if (teams) this.updateTeamsDisplay(teams);
        if (kpis) this.updateKPIs(kpis);
        if (alerts) this.updateAlertsDisplay(alerts);
        
        // Cache data for offline use
        this.cacheData({ operations, berths, teams, kpis, alerts });
    }
    
    async assignVesselToBerth(vesselId, berthNumber) {
        const data = { vessel_id: vesselId, berth_number: berthNumber };
        
        if (this.isOnline) {
            try {
                const response = await fetch('/api/maritime/berths/assign', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    this.showNotification('Berth Assigned', 'Vessel assigned to berth successfully', 'success');
                    await this.refreshDashboardData();
                } else {
                    throw new Error('Assignment failed');
                }
            } catch (error) {
                this.showNotification('Assignment Failed', 'Could not assign vessel to berth', 'error');
            }
        } else {
            // Queue for later sync
            this.pendingUpdates.push({
                type: 'berth_assignment',
                data: data,
                timestamp: Date.now()
            });
            this.showNotification('Queued for Sync', 'Assignment will be processed when online', 'info');
        }
    }
    
    // Modal Methods
    async openOperationDetails(operationId) {
        const modal = document.getElementById('operation-modal');
        const modalBody = document.getElementById('operation-modal-body');
        
        this.showModal(modal);
        modalBody.innerHTML = '<div class="loading-spinner"></div>';
        
        try {
            const response = await fetch(`/api/maritime/operations/${operationId}`);
            const operation = await response.json();
            
            modalBody.innerHTML = this.renderOperationDetails(operation);
        } catch (error) {
            modalBody.innerHTML = '<p class="text-error">Failed to load operation details</p>';
        }
    }
    
    renderOperationDetails(operation) {
        return `
            <div class="operation-details-modal">
                <div class="operation-header">
                    <h3>${operation.vessel_name}</h3>
                    <span class="operation-id">${operation.operation_id}</span>
                </div>
                
                <div class="step-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${operation.progress_percentage}%"></div>
                    </div>
                    <span class="progress-text">${operation.progress_percentage}% Complete</span>
                </div>
                
                <div class="steps-detail">
                    <h4>Step Progress</h4>
                    <div class="step-list">
                        <div class="step-item ${operation.step_1_completed ? 'completed' : ''}">
                            <i class="icon-file-text"></i>
                            <span>Documentation & Arrival</span>
                            ${operation.step_1_completed ? '<i class="icon-check"></i>' : ''}
                        </div>
                        <div class="step-item ${operation.step_2_completed ? 'completed' : ''}">
                            <i class="icon-anchor"></i>
                            <span>Berth Assignment & Positioning</span>
                            ${operation.step_2_completed ? '<i class="icon-check"></i>' : ''}
                        </div>
                        <div class="step-item ${operation.step_3_completed ? 'completed' : ''}">
                            <i class="icon-box"></i>
                            <span>Cargo Operations</span>
                            ${operation.step_3_completed ? '<i class="icon-check"></i>' : ''}
                        </div>
                        <div class="step-item ${operation.step_4_completed ? 'completed' : ''}">
                            <i class="icon-ship"></i>
                            <span>Departure Clearance</span>
                            ${operation.step_4_completed ? '<i class="icon-check"></i>' : ''}
                        </div>
                    </div>
                </div>
                
                <div class="operation-info">
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Operation Type:</label>
                            <span>${operation.operation_type}</span>
                        </div>
                        <div class="info-item">
                            <label>Berth:</label>
                            <span>${operation.berth_assigned || 'Not Assigned'}</span>
                        </div>
                        <div class="info-item">
                            <label>Zone:</label>
                            <span>${operation.zone_assignment || 'TBD'}</span>
                        </div>
                        <div class="info-item">
                            <label>Priority:</label>
                            <span class="priority-${operation.priority}">${operation.priority}</span>
                        </div>
                    </div>
                </div>
                
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="operationsDashboard.updateOperation('${operation.id}')">
                        <i class="icon-edit"></i>
                        Update Operation
                    </button>
                    <button class="btn btn-outline" onclick="operationsDashboard.closeModal('operation-modal')">
                        Close
                    </button>
                </div>
            </div>
        `;
    }
    
    showModal(modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
    
    // Utility Methods
    showLoading(message = 'Loading...') {
        let overlay = document.querySelector('.loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            document.body.appendChild(overlay);
        }
        
        overlay.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-text">${message}</div>
        `;
        overlay.style.display = 'flex';
    }
    
    hideLoading() {
        const overlay = document.querySelector('.loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    showNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="icon-x"></i>
            </button>
        `;
        
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    cacheData(data) {
        if ('localStorage' in window) {
            try {
                localStorage.setItem('operations_dashboard_cache', JSON.stringify({
                    data: data,
                    timestamp: Date.now()
                }));
            } catch (error) {
                console.warn('Could not cache data:', error);
            }
        }
    }
    
    loadCachedData() {
        if ('localStorage' in window) {
            try {
                const cached = JSON.parse(localStorage.getItem('operations_dashboard_cache'));
                if (cached && (Date.now() - cached.timestamp) < 3600000) { // 1 hour
                    this.updateOperationsList(cached.data.operations);
                    this.updateBerthsDisplay(cached.data.berths);
                    this.updateTeamsDisplay(cached.data.teams);
                    this.updateKPIs(cached.data.kpis);
                    return true;
                }
            } catch (error) {
                console.warn('Could not load cached data:', error);
            }
        }
        return false;
    }
    
    async syncPendingUpdates() {
        if (!this.isOnline || this.pendingUpdates.length === 0) return;
        
        console.log(`Syncing ${this.pendingUpdates.length} pending updates...`);
        
        for (const update of this.pendingUpdates) {
            try {
                let endpoint, method, body;
                
                switch (update.type) {
                    case 'berth_assignment':
                        endpoint = '/api/maritime/berths/assign';
                        method = 'POST';
                        body = JSON.stringify(update.data);
                        break;
                    default:
                        continue;
                }
                
                const response = await fetch(endpoint, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: body
                });
                
                if (response.ok) {
                    console.log('Successfully synced update:', update.type);
                } else {
                    throw new Error(`Sync failed: ${response.status}`);
                }
            } catch (error) {
                console.error('Failed to sync update:', update, error);
            }
        }
        
        this.pendingUpdates = [];
        this.showNotification('Sync Complete', 'All pending updates have been processed', 'success');
        await this.refreshDashboardData();
    }
    
    // Public API methods
    dismissAlert(alertId) {
        const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
        if (alertElement) {
            alertElement.remove();
        }
        
        if (this.isOnline) {
            fetch(`/api/maritime/alerts/${alertId}/dismiss`, { method: 'POST' })
                .catch(error => console.error('Failed to dismiss alert:', error));
        }
    }
    
    markAllAlertsRead() {
        const alerts = document.querySelectorAll('.alert-item');
        alerts.forEach(alert => alert.remove());
        
        if (this.isOnline) {
            fetch('/api/maritime/alerts/mark-all-read', { method: 'POST' })
                .catch(error => console.error('Failed to mark alerts as read:', error));
        }
    }
    
    filterOperations(status) {
        const operations = document.querySelectorAll('.operation-card');
        operations.forEach(operation => {
            if (status === 'all') {
                operation.style.display = 'block';
            } else {
                const hasStatus = operation.querySelector(`.status-${status}`) !== null;
                operation.style.display = hasStatus ? 'block' : 'none';
            }
        });
    }
    
    filterByZone(zone) {
        const operations = document.querySelectorAll('.operation-card');
        operations.forEach(operation => {
            if (zone === 'all') {
                operation.style.display = 'block';
            } else {
                const zoneValue = operation.querySelector('.detail-value:nth-child(6)')?.textContent;
                operation.style.display = (zoneValue === zone) ? 'block' : 'none';
            }
        });
    }
    
    filterByShift(shift) {
        // Implementation depends on team data structure
        console.log('Filtering by shift:', shift);
    }
    
    manageBerth(berthNumber) {
        console.log('Managing berth:', berthNumber);
        // Open berth management interface
    }
    
    viewTeamDetails(teamId) {
        console.log('Viewing team details:', teamId);
        // Open team details modal
    }
    
    initializeOperation() {
        console.log('Initializing new operation');
        // Open new operation wizard
    }
    
    updateOperation(operationId) {
        console.log('Updating operation:', operationId);
        // Open operation update interface
    }
}

// Global functions for HTML onclick handlers
function refreshDashboard() {
    operationsDashboard.refreshDashboard();
}

function initializeOperation() {
    operationsDashboard.initializeOperation();
}

function manageBerth(berthNumber) {
    operationsDashboard.manageBerth(berthNumber);
}

function openOperationDetails(operationId) {
    operationsDashboard.openOperationDetails(operationId);
}

function updateOperation(operationId) {
    operationsDashboard.updateOperation(operationId);
}

function viewTeamDetails(teamId) {
    operationsDashboard.viewTeamDetails(teamId);
}

function dismissAlert(alertId) {
    operationsDashboard.dismissAlert(alertId);
}

function markAllAlertsRead() {
    operationsDashboard.markAllAlertsRead();
}

function filterOperations(status) {
    operationsDashboard.filterOperations(status);
}

function filterByZone(zone) {
    operationsDashboard.filterByZone(zone);
}

function filterByShift(shift) {
    operationsDashboard.filterByShift(shift);
}

function closeModal(modalId) {
    operationsDashboard.closeModal(modalId);
}

function assignToBerth(vesselId) {
    // This could open a modal for berth selection or use drag & drop
    console.log('Assigning vessel to berth:', vesselId);
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.operationsDashboard = new OperationsDashboard();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OperationsDashboard;
}