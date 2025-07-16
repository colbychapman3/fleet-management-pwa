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
        
        // Touch interface properties
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        this.draggedElement = null;
        this.dragStarted = false;
        this.pullToRefreshActive = false;
        this.pullToRefreshThreshold = 80;
        this.lastTouchTime = 0;
        this.hapticFeedbackEnabled = 'vibrate' in navigator;
        
        this.init();
        this.setupEventListeners();
        this.setupWebSocket();
        this.setupOfflineSync();
        this.setupTouchInterface();
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
    
    setupTouchInterface() {
        if (!this.isTouch) return;
        
        // Setup pull-to-refresh
        this.setupPullToRefresh();
        
        // Setup mobile navigation
        this.setupMobileNavigation();
        
        // Setup touch-friendly drag and drop
        this.setupTouchDragAndDrop();
        
        // Setup swipe gestures
        this.setupSwipeGestures();
        
        // Setup haptic feedback
        this.setupHapticFeedback();
        
        console.log('Touch interface initialized');
    }
    
    setupPullToRefresh() {
        const mainContent = document.querySelector('.main-content') || document.body;
        let pullStartY = 0;
        let pullCurrentY = 0;
        let pullDistance = 0;
        let pulling = false;
        
        const pullIndicator = document.createElement('div');
        pullIndicator.className = 'pull-to-refresh-indicator';
        pullIndicator.innerHTML = '<i class="icon-refresh"></i>';
        mainContent.appendChild(pullIndicator);
        
        mainContent.addEventListener('touchstart', (e) => {
            if (mainContent.scrollTop === 0) {
                pullStartY = e.touches[0].clientY;
                pulling = true;
            }
        });
        
        mainContent.addEventListener('touchmove', (e) => {
            if (!pulling) return;
            
            pullCurrentY = e.touches[0].clientY;
            pullDistance = pullCurrentY - pullStartY;
            
            if (pullDistance > 0) {
                e.preventDefault();
                const progress = Math.min(pullDistance / this.pullToRefreshThreshold, 1);
                
                pullIndicator.style.transform = `translateY(${pullDistance * 0.5}px) scale(${progress})`;
                pullIndicator.style.opacity = progress;
                
                if (pullDistance >= this.pullToRefreshThreshold) {
                    mainContent.classList.add('pulling');
                    this.triggerHapticFeedback('light');
                }
            }
        });
        
        mainContent.addEventListener('touchend', () => {
            if (!pulling) return;
            
            pulling = false;
            pullIndicator.style.transform = '';
            pullIndicator.style.opacity = '';
            mainContent.classList.remove('pulling');
            
            if (pullDistance >= this.pullToRefreshThreshold) {
                this.pullToRefreshActive = true;
                mainContent.classList.add('refreshing');
                this.triggerHapticFeedback('medium');
                
                this.refreshDashboard().finally(() => {
                    this.pullToRefreshActive = false;
                    mainContent.classList.remove('refreshing');
                });
            }
        });
    }
    
    setupMobileNavigation() {
        // Auto-hide mobile header on scroll
        let lastScrollY = window.scrollY;
        const mobileHeader = document.querySelector('.mobile-header');
        
        if (mobileHeader) {
            window.addEventListener('scroll', () => {
                const currentScrollY = window.scrollY;
                
                if (currentScrollY > lastScrollY && currentScrollY > 100) {
                    mobileHeader.classList.add('hidden');
                } else {
                    mobileHeader.classList.remove('hidden');
                }
                
                lastScrollY = currentScrollY;
            });
        }
    }
    
    setupTouchDragAndDrop() {
        const queueItems = document.querySelectorAll('.queue-item');
        const berths = document.querySelectorAll('.berth');
        
        queueItems.forEach(item => {
            this.makeItemTouchDraggable(item);
        });
        
        berths.forEach(berth => {
            this.makeItemTouchDroppable(berth);
        });
    }
    
    makeItemTouchDraggable(item) {
        let isDragging = false;
        let startX, startY, currentX, currentY;
        let dragClone = null;
        
        const touchStart = (e) => {
            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
            
            setTimeout(() => {
                if (!isDragging) {
                    isDragging = true;
                    this.draggedElement = item;
                    
                    // Create visual feedback
                    dragClone = item.cloneNode(true);
                    dragClone.style.position = 'fixed';
                    dragClone.style.pointerEvents = 'none';
                    dragClone.style.zIndex = '9999';
                    dragClone.style.opacity = '0.8';
                    dragClone.style.transform = 'scale(1.1)';
                    document.body.appendChild(dragClone);
                    
                    item.classList.add('dragging');
                    this.triggerHapticFeedback('medium');
                }
            }, 200);
        };
        
        const touchMove = (e) => {
            if (!isDragging) return;
            
            e.preventDefault();
            const touch = e.touches[0];
            currentX = touch.clientX;
            currentY = touch.clientY;
            
            if (dragClone) {
                dragClone.style.left = `${currentX - 50}px`;
                dragClone.style.top = `${currentY - 30}px`;
            }
            
            // Highlight drop targets
            const elementBelow = document.elementFromPoint(currentX, currentY);
            const berth = elementBelow?.closest('.berth');
            
            document.querySelectorAll('.berth').forEach(b => b.classList.remove('drag-over'));
            if (berth) {
                berth.classList.add('drag-over');
            }
        };
        
        const touchEnd = (e) => {
            if (!isDragging) return;
            
            isDragging = false;
            item.classList.remove('dragging');
            
            if (dragClone) {
                dragClone.remove();
                dragClone = null;
            }
            
            const touch = e.changedTouches[0];
            const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
            const berth = elementBelow?.closest('.berth');
            
            document.querySelectorAll('.berth').forEach(b => b.classList.remove('drag-over'));
            
            if (berth) {
                const vesselId = item.dataset.vesselId;
                const berthNumber = berth.id.split('-')[1];
                this.assignVesselToBerth(vesselId, berthNumber);
                this.triggerHapticFeedback('success');
            }
            
            this.draggedElement = null;
        };
        
        item.addEventListener('touchstart', touchStart);
        item.addEventListener('touchmove', touchMove);
        item.addEventListener('touchend', touchEnd);
    }
    
    makeItemTouchDroppable(berth) {
        berth.addEventListener('touchmove', (e) => {
            if (this.draggedElement) {
                e.preventDefault();
                berth.classList.add('drag-over');
            }
        });
        
        berth.addEventListener('touchend', () => {
            berth.classList.remove('drag-over');
        });
    }
    
    setupSwipeGestures() {
        // Setup swipe gestures for cards and list items
        const swipeableElements = document.querySelectorAll('.operation-card, .alert-item, .queue-item');
        
        swipeableElements.forEach(element => {
            this.makeElementSwipeable(element);
        });
    }
    
    makeElementSwipeable(element) {
        let startX, startY, currentX, currentY;
        let isSwipeActive = false;
        let swipeDirection = null;
        
        const touchStart = (e) => {
            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
            isSwipeActive = true;
        };
        
        const touchMove = (e) => {
            if (!isSwipeActive) return;
            
            const touch = e.touches[0];
            currentX = touch.clientX;
            currentY = touch.clientY;
            
            const deltaX = currentX - startX;
            const deltaY = currentY - startY;
            
            // Determine swipe direction
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 30) {
                swipeDirection = deltaX > 0 ? 'right' : 'left';
                
                // Prevent scrolling during horizontal swipe
                e.preventDefault();
                
                // Apply visual feedback
                const translateX = Math.min(Math.abs(deltaX), 100) * (deltaX > 0 ? 1 : -1);
                element.style.transform = `translateX(${translateX}px)`;
                element.style.opacity = 1 - Math.abs(deltaX) / 200;
            }
        };
        
        const touchEnd = (e) => {
            if (!isSwipeActive) return;
            
            isSwipeActive = false;
            element.style.transform = '';
            element.style.opacity = '';
            
            const deltaX = currentX - startX;
            
            if (Math.abs(deltaX) > 100) {
                this.handleSwipeGesture(element, swipeDirection);
                this.triggerHapticFeedback('light');
            }
            
            swipeDirection = null;
        };
        
        element.addEventListener('touchstart', touchStart);
        element.addEventListener('touchmove', touchMove);
        element.addEventListener('touchend', touchEnd);
    }
    
    handleSwipeGesture(element, direction) {
        const elementType = element.className.split(' ')[0];
        
        switch (elementType) {
            case 'operation-card':
                if (direction === 'right') {
                    // Quick action: View details
                    const operationId = element.dataset.operationId;
                    this.openOperationDetails(operationId);
                } else if (direction === 'left') {
                    // Quick action: Update status
                    const operationId = element.dataset.operationId;
                    this.updateOperation(operationId);
                }
                break;
                
            case 'alert-item':
                if (direction === 'right') {
                    // Dismiss alert
                    const alertId = element.dataset.alertId;
                    this.dismissAlert(alertId);
                } else if (direction === 'left') {
                    // Mark as read
                    element.style.opacity = '0.5';
                }
                break;
                
            case 'queue-item':
                if (direction === 'right') {
                    // Show berth selection
                    const vesselId = element.dataset.vesselId;
                    this.showBerthSelectionModal(vesselId);
                }
                break;
        }
    }
    
    setupHapticFeedback() {
        if (!this.hapticFeedbackEnabled) return;
        
        // Add haptic feedback to buttons
        document.querySelectorAll('.btn, button').forEach(button => {
            button.addEventListener('touchstart', () => {
                this.triggerHapticFeedback('light');
            });
        });
    }
    
    triggerHapticFeedback(type) {
        if (!this.hapticFeedbackEnabled) return;
        
        const patterns = {
            light: 10,
            medium: 50,
            heavy: 100,
            success: [10, 50, 10],
            error: [100, 50, 100, 50, 100]
        };
        
        const pattern = patterns[type] || patterns.light;
        
        try {
            if (Array.isArray(pattern)) {
                navigator.vibrate(pattern);
            } else {
                navigator.vibrate(pattern);
            }
        } catch (error) {
            console.warn('Haptic feedback failed:', error);
        }
    }
    
    setupDragAndDrop() {
        // Desktop drag and drop fallback
        if (this.isTouch) {
            this.setupTouchDragAndDrop();
            return;
        }
        
        // Original desktop drag and drop code
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
                console.log('Auto-refreshing dashboard data...');
                this.refreshDashboardData().catch(error => {
                    console.error('Auto-refresh failed:', error);
                });
            }
        }, 30000);
        
        console.log('Real-time polling enabled: Dashboard will refresh every 30 seconds');
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
            '/maritime/api/operations',
            '/maritime/berth/status',
            '/api/maritime/teams/performance',
            '/api/maritime/kpis',
            '/api/maritime/alerts/active'
        ];
        
        const promises = endpoints.map(async (endpoint) => {
            try {
                const response = await fetch(endpoint);
                return response.ok ? await response.json() : null;
            } catch (error) {
                console.warn(`Failed to fetch ${endpoint}:`, error);
                return null;
            }
        });
        
        const [operations, berths, teams, kpis, alerts] = await Promise.all(promises);
        
        // Update each section with proper error handling
        try {
            if (operations) this.updateOperationsList(operations);
        } catch (error) {
            console.error('Error updating operations list:', error);
        }
        
        try {
            if (berths) this.updateBerthsDisplay(berths);
        } catch (error) {
            console.error('Error updating berths display:', error);
        }
        
        try {
            if (teams) this.updateTeamsDisplay(teams);
        } catch (error) {
            console.error('Error updating teams display:', error);
        }
        
        try {
            if (kpis) this.updateKPIMetrics(kpis);
        } catch (error) {
            console.error('Error updating KPIs:', error);
        }
        
        try {
            if (alerts) this.updateAlertsDisplay(alerts);
        } catch (error) {
            console.error('Error updating alerts:', error);
        }
        
        // Cache data for offline use
        this.cacheData({ operations, berths, teams, kpis, alerts });
        
        // Update last refresh time
        this.lastUpdateTime = new Date();
        this.updateLastUpdateTime();
    }
    
    async assignVesselToBerth(vesselId, berthNumber) {
        const data = { vessel_id: vesselId, berth_number: berthNumber };
        
        if (this.isOnline) {
            try {
                this.showLoading('Assigning vessel to berth...');
                
                const response = await fetch('/maritime/berth/assign', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    // Update UI immediately on success
                    this.updateBerthAssignmentUI(vesselId, berthNumber, result.operation);
                    
                    this.showNotification('Berth Assigned', result.message, 'success');
                    
                    // Refresh berth status display
                    await this.refreshBerthStatus();
                    await this.refreshVesselQueue();
                } else {
                    throw new Error(result.error || 'Assignment failed');
                }
            } catch (error) {
                console.error('Berth assignment error:', error);
                this.showNotification('Assignment Failed', error.message || 'Could not assign vessel to berth', 'error');
            } finally {
                this.hideLoading();
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
    
    // Berth Management Methods
    async refreshBerthStatus() {
        try {
            const response = await fetch('/maritime/berth/status');
            if (response.ok) {
                const data = await response.json();
                this.updateBerthsDisplay(data);
            }
        } catch (error) {
            console.error('Error refreshing berth status:', error);
        }
    }

    async refreshVesselQueue() {
        try {
            const response = await fetch('/maritime/berth/status');
            if (response.ok) {
                const data = await response.json();
                this.updateVesselQueueDisplay(data.queue);
            }
        } catch (error) {
            console.error('Error refreshing vessel queue:', error);
        }
    }

    updateBerthAssignmentUI(vesselId, berthNumber, operationData) {
        // Remove vessel from queue
        const queueItem = document.querySelector(`[data-vessel-id="${vesselId}"]`);
        if (queueItem) {
            queueItem.remove();
        }

        // Update berth display
        const berth = document.getElementById(`berth-${berthNumber}`);
        if (berth && operationData) {
            berth.classList.remove('berth-available');
            berth.classList.add('berth-occupied');
            
            this.renderBerthVesselInfo(berth, {
                name: operationData.vessel_name,
                type: 'Cargo Vessel',
                progress: 0
            });
        }
    }

    showBerthManagementModal(berth, queue) {
        const modal = document.getElementById('berth-assignment-modal');
        const modalBody = document.getElementById('berth-assignment-modal-body');
        
        if (!modal || !modalBody) {
            console.error('Berth management modal not found');
            return;
        }
        
        const modalContent = this.renderBerthManagementContent(berth, queue);
        modalBody.innerHTML = modalContent;
        
        this.showModal(modal);
    }

    renderBerthManagementContent(berth, queue) {
        const isOccupied = berth.status === 'occupied';
        const vesselInfo = berth.vessel || {};
        
        let content = `
            <div class="berth-management-content">
                <div class="berth-info">
                    <h4>Berth ${berth.berth_number} Management</h4>
                    <div class="berth-status-overview">
                        <span class="status-badge status-${berth.status}">
                            ${berth.status.charAt(0).toUpperCase() + berth.status.slice(1)}
                        </span>
                        <span class="capacity-info">Capacity: ${berth.capacity} vessel(s)</span>
                        <span class="utilization-info">Utilization: ${Math.round(berth.utilization * 100)}%</span>
                    </div>
                </div>
        `;
        
        if (isOccupied && vesselInfo.name) {
            content += `
                <div class="current-assignment">
                    <h5>Current Assignment</h5>
                    <div class="vessel-details">
                        <div class="vessel-name">${vesselInfo.name}</div>
                        <div class="vessel-type">${vesselInfo.type || 'Unknown'}</div>
                        <div class="progress-info">
                            <span>Progress: ${vesselInfo.progress || 0}%</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${vesselInfo.progress || 0}%"></div>
                            </div>
                        </div>
                    </div>
                    <div class="berth-actions">
                        <button class="btn btn-warning" onclick="operationsDashboard.unassignFromBerth('${vesselInfo.id}', '${berth.berth_number}')">
                            <i class="icon-x"></i>
                            Remove from Berth
                        </button>
                    </div>
                </div>
            `;
        }
        
        if (queue && queue.length > 0) {
            content += `
                <div class="reassignment-options">
                    <h5>Available Vessels for Assignment</h5>
                    <div class="vessel-queue-list">
            `;
            
            queue.forEach(vessel => {
                content += `
                    <div class="queue-vessel-item">
                        <div class="vessel-info">
                            <div class="vessel-name">${vessel.vessel_name}</div>
                            <div class="vessel-details">
                                <span class="vessel-type">${vessel.vessel_type}</span>
                                <span class="eta">ETA: ${vessel.eta || 'TBD'}</span>
                                <span class="waiting-time">Waiting: ${Math.round(vessel.waiting_time || 0)}h</span>
                            </div>
                        </div>
                        <button class="btn btn-primary btn-sm" 
                                onclick="operationsDashboard.assignFromModal('${vessel.vessel_id}', '${berth.berth_number}')"
                                ${isOccupied ? 'disabled title="Berth is currently occupied"' : ''}>
                            <i class="icon-dock"></i>
                            Assign to Berth
                        </button>
                    </div>
                `;
            });
            
            content += `
                    </div>
                </div>
            `;
        }
        
        content += `
                <div class="modal-actions">
                    <button class="btn btn-outline" onclick="operationsDashboard.closeModal('berth-assignment-modal')">
                        Close
                    </button>
                </div>
            </div>
        `;
        
        return content;
    }

    showBerthSelectionModal(vesselId) {
        fetch('/maritime/berth/status')
            .then(response => response.json())
            .then(data => {
                const modal = document.getElementById('berth-assignment-modal');
                const modalBody = document.getElementById('berth-assignment-modal-body');
                
                if (!modal || !modalBody) return;
                
                const content = this.renderBerthSelectionContent(vesselId, data.berths);
                modalBody.innerHTML = content;
                
                this.showModal(modal);
            })
            .catch(error => {
                console.error('Error loading berth selection:', error);
                this.showNotification('Error', 'Failed to load berth options', 'error');
            });
    }

    renderBerthSelectionContent(vesselId, berths) {
        let content = `
            <div class="berth-selection-content">
                <h4>Select Berth for Vessel Assignment</h4>
                <div class="berth-options">
        `;
        
        berths.forEach(berth => {
            const isAvailable = berth.status === 'available';
            const disabled = !isAvailable ? 'disabled' : '';
            const statusText = isAvailable ? 'Available' : `Occupied by ${berth.vessel?.name || 'Unknown'}`;
            
            content += `
                <div class="berth-option ${!isAvailable ? 'berth-disabled' : ''}">
                    <div class="berth-info">
                        <h5>Berth ${berth.berth_number}</h5>
                        <div class="berth-status">
                            <span class="status-badge status-${berth.status}">${statusText}</span>
                            <span class="utilization">Utilization: ${Math.round(berth.utilization * 100)}%</span>
                        </div>
                    </div>
                    <button class="btn btn-primary" 
                            onclick="operationsDashboard.assignFromModal('${vesselId}', '${berth.berth_number}')"
                            ${disabled}>
                        <i class="icon-dock"></i>
                        Assign to This Berth
                    </button>
                </div>
            `;
        });
        
        content += `
                </div>
                <div class="modal-actions">
                    <button class="btn btn-outline" onclick="operationsDashboard.closeModal('berth-assignment-modal')">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        return content;
    }

    async assignFromModal(vesselId, berthNumber) {
        await this.assignVesselToBerth(vesselId, berthNumber);
        this.closeModal('berth-assignment-modal');
    }

    async unassignFromBerth(vesselId, berthNumber) {
        try {
            this.showLoading('Removing vessel from berth...');
            
            const response = await fetch('/maritime/berth/unassign', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vessel_id: vesselId })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showNotification('Berth Cleared', result.message, 'success');
                await this.refreshBerthStatus();
                await this.refreshVesselQueue();
                this.closeModal('berth-assignment-modal');
            } else {
                throw new Error(result.error || 'Failed to remove vessel from berth');
            }
        } catch (error) {
            console.error('Berth unassignment error:', error);
            this.showNotification('Error', error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // UI Update Methods
    updateOperationsList(operations) {
        const operationsList = document.getElementById('operations-list');
        if (!operationsList || !operations) return;
        
        // Handle both array and object responses
        const operationsArray = Array.isArray(operations) ? operations : operations.operations || [];
        
        if (operationsArray.length === 0) {
            operationsList.innerHTML = '<div class="no-operations">No active operations</div>';
            return;
        }
        
        operationsList.innerHTML = operationsArray.map(op => this.renderOperationCard(op)).join('');
    }

    renderOperationCard(operation) {
        const vessel = operation.vessel || {};
        const wizardProgress = operation.wizard_progress || {};
        
        return `
            <div class="operation-card" data-operation-id="${operation.vessel?.id || operation.id}">
                <div class="operation-header">
                    <div class="operation-title">
                        <h4>${vessel.name || 'Unknown Vessel'}</h4>
                        <span class="operation-id">${wizardProgress.operation_id || 'N/A'}</span>
                    </div>
                    <div class="operation-status">
                        <span class="status-badge status-${vessel.status || 'unknown'}">
                            ${(vessel.status || 'unknown').replace('_', ' ').charAt(0).toUpperCase() + (vessel.status || 'unknown').slice(1)}
                        </span>
                    </div>
                </div>
                
                <div class="operation-progress">
                    <div class="progress-header">
                        <span class="step-info">Step ${wizardProgress.current_step || 1}</span>
                        <span class="progress-percentage">${this.calculateOperationProgress(wizardProgress)}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${this.calculateOperationProgress(wizardProgress)}%"></div>
                    </div>
                    
                    <div class="step-indicators">
                        ${this.renderStepIndicators(wizardProgress)}
                    </div>
                </div>
                
                <div class="operation-details">
                    <div class="detail-row">
                        <span class="detail-label">Berth:</span>
                        <span class="detail-value">${vessel.berth_number ? `Berth ${vessel.berth_number}` : 'Not Assigned'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Vessel Type:</span>
                        <span class="detail-value">${vessel.vessel_type || 'Unknown'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">ETA:</span>
                        <span class="detail-value">${vessel.arrival_date ? new Date(vessel.arrival_date).toLocaleString() : 'TBD'}</span>
                    </div>
                </div>
                
                <div class="operation-actions">
                    <button class="btn btn-sm btn-primary" onclick="operationsDashboard.openOperationDetails('${vessel.id}')">
                        <i class="icon-eye"></i>
                        View Details
                    </button>
                </div>
            </div>
        `;
    }

    renderStepIndicators(wizardProgress) {
        const steps = [
            { key: 'step_1_completed', icon: 'file-text', title: 'Documentation' },
            { key: 'step_2_completed', icon: 'anchor', title: 'Positioning' },
            { key: 'step_3_completed', icon: 'box', title: 'Cargo Operations' },
            { key: 'step_4_completed', icon: 'ship', title: 'Departure' }
        ];
        
        return steps.map((step, index) => {
            const stepNumber = index + 1;
            const isCompleted = wizardProgress[step.key];
            const isActive = wizardProgress.current_step === stepNumber;
            const className = isCompleted ? 'completed' : (isActive ? 'active' : 'pending');
            
            return `
                <div class="step-indicator ${className}" title="${step.title}">
                    <i class="icon-${step.icon}"></i>
                    <span>${stepNumber}</span>
                </div>
            `;
        }).join('');
    }

    calculateOperationProgress(wizardProgress) {
        const completedSteps = [
            wizardProgress.step_1_completed,
            wizardProgress.step_2_completed,
            wizardProgress.step_3_completed,
            wizardProgress.step_4_completed
        ].filter(Boolean).length;
        
        return Math.round((completedSteps / 4) * 100);
    }

    updateBerthsDisplay(berthData) {
        if (!berthData || !berthData.berths) return;
        
        berthData.berths.forEach(berth => {
            const berthElement = document.getElementById(`berth-${berth.berth_number}`);
            if (berthElement) {
                this.updateBerthElement(berthElement, berth);
            }
        });
        
        // Update vessel queue
        if (berthData.queue) {
            this.updateVesselQueueDisplay(berthData.queue);
        }
    }

    updateBerthElement(berthElement, berthData) {
        // Update status classes
        berthElement.classList.remove('berth-available', 'berth-occupied', 'berth-maintenance');
        berthElement.classList.add(`berth-${berthData.status}`);
        
        // Update content
        if (berthData.status === 'occupied' && berthData.vessel) {
            this.renderBerthVesselInfo(berthElement, berthData.vessel);
        } else {
            this.renderEmptyBerth(berthElement);
        }
    }

    updateVesselQueueDisplay(queue) {
        const queueContainer = document.getElementById('vessel-queue');
        if (!queueContainer || !queue) return;
        
        if (queue.length === 0) {
            queueContainer.innerHTML = '<div class="no-queue-items">No vessels in queue</div>';
            return;
        }
        
        queueContainer.innerHTML = queue.map(vessel => `
            <div class="queue-item" data-vessel-id="${vessel.vessel_id}">
                <div class="vessel-info">
                    <div class="vessel-name">${vessel.vessel_name}</div>
                    <div class="vessel-details">
                        <span class="eta">ETA: ${vessel.eta || 'TBD'}</span>
                        <span class="cargo-type">${vessel.operation_type || 'Unknown'}</span>
                        <span class="waiting-time">Waiting: ${Math.round(vessel.waiting_time || 0)}h</span>
                    </div>
                </div>
                <div class="queue-actions">
                    <button class="btn btn-sm btn-primary" onclick="assignToBerth('${vessel.vessel_id}')">
                        <i class="icon-dock"></i>
                        Assign Berth
                    </button>
                </div>
            </div>
        `).join('');
    }

    updateTeamsDisplay(teams) {
        // Implementation for team performance updates
        if (!teams) return;
        
        console.log('Updating teams display:', teams);
        
        // Handle both object and array formats
        const teamsData = teams.team_performance || teams.active_teams || teams;
        if (!teamsData) return;
        
        // Update team metrics container
        const teamMetricsContainer = document.getElementById('team-metrics');
        if (teamMetricsContainer) {
            this.renderTeamPerformanceCards(teamMetricsContainer, teamsData);
        }
        
        // Update team performance alerts
        this.updateTeamPerformanceAlerts(teamsData);
        
        // Update team performance chart
        this.updateTeamPerformanceChart(teamsData);
    }
    
    renderTeamPerformanceCards(container, teamsData) {
        if (!Array.isArray(teamsData) || teamsData.length === 0) {
            container.innerHTML = '<div class="no-teams">No active teams</div>';
            return;
        }
        
        container.innerHTML = teamsData.map(team => `
            <div class="team-card" data-team-id="${team.team_id}">
                <div class="team-card-header">
                    <div class="team-name">${team.team_name || `Team ${team.team_id}`}</div>
                    <div class="team-status">
                        <span class="status-dot status-${team.status || 'active'}"></span>
                        <span class="status-text">${(team.status || 'active').replace('_', ' ')}</span>
                    </div>
                </div>
                
                <div class="team-assignment">
                    ${team.current_operation ? `
                        <div class="assignment-info">
                            <i class="icon-ship"></i>
                            <span class="vessel-name">${team.current_operation.vessel_name}</span>
                            <span class="operation-type">${team.current_operation.operation_type}</span>
                        </div>
                        <div class="assignment-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${team.current_operation.progress || 0}%"></div>
                            </div>
                            <span class="progress-text">${team.current_operation.progress || 0}%</span>
                        </div>
                    ` : `
                        <div class="no-assignment">
                            <i class="icon-clock"></i>
                            <span>Available for assignment</span>
                        </div>
                    `}
                </div>
                
                <div class="team-metrics">
                    <div class="metric">
                        <div class="metric-label">Efficiency</div>
                        <div class="metric-value ${this.getEfficiencyClass(team.performance?.efficiency || 0)}">
                            ${Math.round(team.performance?.efficiency || 0)}%
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Throughput</div>
                        <div class="metric-value">
                            ${Math.round(team.performance?.throughput_rate || 0)} MT/h
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Safety</div>
                        <div class="metric-value ${this.getSafetyClass(team.performance?.safety_incidents || 0)}">
                            ${team.performance?.safety_incidents || 0} incidents
                        </div>
                    </div>
                </div>
                
                <div class="team-details">
                    <div class="detail-item">
                        <span class="detail-label">Team Size:</span>
                        <span class="detail-value">${team.team_size || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Lead:</span>
                        <span class="detail-value">${team.lead_name || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Shift:</span>
                        <span class="detail-value">${this.formatShiftTime(team.shift_start, team.shift_end)}</span>
                    </div>
                </div>
                
                <div class="team-actions">
                    <button class="btn btn-sm btn-primary" onclick="operationsDashboard.viewTeamDetails('${team.team_id}')">
                        <i class="icon-eye"></i>
                        Details
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="operationsDashboard.editTeamPerformance('${team.team_id}')">
                        <i class="icon-edit"></i>
                        Update
                    </button>
                </div>
            </div>
        `).join('');
        
        // Remove skeleton loader
        const skeleton = document.getElementById('team-loading');
        if (skeleton) skeleton.remove();
    }
    
    getEfficiencyClass(efficiency) {
        if (efficiency >= 90) return 'metric-excellent';
        if (efficiency >= 80) return 'metric-good';
        if (efficiency >= 70) return 'metric-average';
        return 'metric-poor';
    }
    
    getSafetyClass(incidents) {
        if (incidents === 0) return 'metric-excellent';
        if (incidents <= 1) return 'metric-good';
        if (incidents <= 2) return 'metric-average';
        return 'metric-poor';
    }
    
    formatShiftTime(start, end) {
        if (!start || !end) return 'N/A';
        return `${start} - ${end}`;
    }
    
    updateTeamPerformanceAlerts(teamsData) {
        const alertContainer = document.getElementById('team-alert-items');
        if (!alertContainer) return;
        
        const alerts = [];
        
        teamsData.forEach(team => {
            const efficiency = team.performance?.efficiency || 0;
            const safetyIncidents = team.performance?.safety_incidents || 0;
            const throughput = team.performance?.throughput_rate || 0;
            
            // Check for low efficiency
            if (efficiency < 70) {
                alerts.push({
                    type: 'warning',
                    team: team.team_name || `Team ${team.team_id}`,
                    message: `Low efficiency: ${Math.round(efficiency)}%`,
                    icon: 'trending-down'
                });
            }
            
            // Check for safety incidents
            if (safetyIncidents > 0) {
                alerts.push({
                    type: 'error',
                    team: team.team_name || `Team ${team.team_id}`,
                    message: `${safetyIncidents} safety incidents`,
                    icon: 'alert-triangle'
                });
            }
            
            // Check for low throughput
            if (throughput < 100) {
                alerts.push({
                    type: 'info',
                    team: team.team_name || `Team ${team.team_id}`,
                    message: `Low throughput: ${Math.round(throughput)} MT/h`,
                    icon: 'trending-down'
                });
            }
        });
        
        if (alerts.length === 0) {
            alertContainer.innerHTML = '<div class="no-alerts">No performance alerts</div>';
        } else {
            alertContainer.innerHTML = alerts.map(alert => `
                <div class="alert-item alert-${alert.type}">
                    <i class="icon-${alert.icon}"></i>
                    <div class="alert-content">
                        <span class="alert-team">${alert.team}</span>
                        <span class="alert-message">${alert.message}</span>
                    </div>
                </div>
            `).join('');
        }
    }
    
    updateTeamPerformanceChart(teamsData) {
        const chartCanvas = document.getElementById('teamPerformanceChart');
        if (!chartCanvas) return;
        
        // Simple chart implementation - in production you'd use a library like Chart.js
        const ctx = chartCanvas.getContext('2d');
        ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
        
        if (!teamsData || teamsData.length === 0) {
            ctx.fillStyle = '#888';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', chartCanvas.width / 2, chartCanvas.height / 2);
            return;
        }
        
        // Draw simple bar chart for efficiency
        const barWidth = chartCanvas.width / teamsData.length;
        const maxHeight = chartCanvas.height - 40;
        
        teamsData.forEach((team, index) => {
            const efficiency = team.performance?.efficiency || 0;
            const barHeight = (efficiency / 100) * maxHeight;
            const x = index * barWidth;
            
            // Draw bar
            ctx.fillStyle = this.getEfficiencyColor(efficiency);
            ctx.fillRect(x + 5, chartCanvas.height - barHeight - 20, barWidth - 10, barHeight);
            
            // Draw label
            ctx.fillStyle = '#333';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(
                `${team.team_name || `T${team.team_id}`}`,
                x + barWidth / 2,
                chartCanvas.height - 5
            );
            
            // Draw value
            ctx.fillStyle = '#fff';
            ctx.font = '10px Arial';
            ctx.fillText(
                `${Math.round(efficiency)}%`,
                x + barWidth / 2,
                chartCanvas.height - barHeight - 25
            );
        });
    }
    
    getEfficiencyColor(efficiency) {
        if (efficiency >= 90) return '#4CAF50';
        if (efficiency >= 80) return '#8BC34A';
        if (efficiency >= 70) return '#FFC107';
        return '#F44336';
    }
    
    // Team Assignment Modal Functions
    async showTeamAssignmentModal() {
        const modal = document.getElementById('team-assignment-modal');
        if (!modal) return;
        
        try {
            // Load active operations
            const operationsResponse = await fetch('/api/maritime/operations');
            const operationsData = await operationsResponse.json();
            
            const operationSelect = document.getElementById('operation-select');
            if (operationSelect) {
                operationSelect.innerHTML = '<option value="">Select an operation...</option>';
                
                if (operationsData.operations) {
                    operationsData.operations.forEach(op => {
                        operationSelect.innerHTML += `
                            <option value="${op.id}">${op.vessel_name} - ${op.operation_type}</option>
                        `;
                    });
                }
            }
            
            this.showModal(modal);
        } catch (error) {
            console.error('Error loading team assignment modal:', error);
            this.showNotification('Error', 'Failed to load team assignment interface', 'error');
        }
    }
    
    async loadOperationDetails() {
        const operationSelect = document.getElementById('operation-select');
        const operationId = operationSelect.value;
        
        if (!operationId) {
            document.getElementById('operation-details').style.display = 'none';
            document.getElementById('team-selection').style.display = 'none';
            document.getElementById('selected-teams').style.display = 'none';
            document.getElementById('assignment-options').style.display = 'none';
            return;
        }
        
        try {
            // Load operation details
            const response = await fetch(`/api/maritime/operations/${operationId}`);
            const operation = await response.json();
            
            // Update operation details
            document.getElementById('vessel-name').textContent = operation.vessel_name;
            document.getElementById('operation-type').textContent = operation.operation_type;
            document.getElementById('berth-location').textContent = operation.berth || 'Not assigned';
            
            // Load current teams
            const currentTeams = operation.assigned_teams || [];
            document.getElementById('current-teams').textContent = 
                currentTeams.length > 0 ? currentTeams.join(', ') : 'None';
            
            // Show operation details
            document.getElementById('operation-details').style.display = 'block';
            
            // Load available teams
            await this.loadAvailableTeams();
            
            document.getElementById('team-selection').style.display = 'block';
            document.getElementById('selected-teams').style.display = 'block';
            document.getElementById('assignment-options').style.display = 'block';
            
        } catch (error) {
            console.error('Error loading operation details:', error);
            this.showNotification('Error', 'Failed to load operation details', 'error');
        }
    }
    
    async loadAvailableTeams() {
        try {
            const response = await fetch('/api/maritime/teams/active');
            const teamsData = await response.json();
            
            const teamsContainer = document.getElementById('available-teams');
            if (!teamsContainer) return;
            
            if (!teamsData.active_teams || teamsData.active_teams.length === 0) {
                teamsContainer.innerHTML = '<div class="no-teams">No available teams</div>';
                return;
            }
            
            teamsContainer.innerHTML = teamsData.active_teams.map(team => `
                <div class="team-selection-card" data-team-id="${team.id}">
                    <div class="team-info">
                        <h5>${team.team_name}</h5>
                        <div class="team-meta">
                            <span class="team-size">${team.team_size} members</span>
                            <span class="team-lead">${team.lead_name || 'No lead'}</span>
                        </div>
                        <div class="team-performance">
                            <div class="performance-metric">
                                <span class="metric-label">Efficiency:</span>
                                <span class="metric-value">${Math.round(team.performance?.efficiency || 0)}%</span>
                            </div>
                            <div class="performance-metric">
                                <span class="metric-label">Throughput:</span>
                                <span class="metric-value">${Math.round(team.performance?.throughput_rate || 0)} MT/h</span>
                            </div>
                        </div>
                    </div>
                    <div class="team-actions">
                        <button class="btn btn-sm btn-primary" onclick="operationsDashboard.selectTeam('${team.id}')">
                            <i class="icon-plus"></i>
                            Select
                        </button>
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            console.error('Error loading available teams:', error);
            this.showNotification('Error', 'Failed to load available teams', 'error');
        }
    }
    
    selectedTeamIds = new Set();
    
    selectTeam(teamId) {
        if (this.selectedTeamIds.has(teamId)) {
            this.selectedTeamIds.delete(teamId);
        } else {
            this.selectedTeamIds.add(teamId);
        }
        
        this.updateTeamSelection();
        this.updateSelectedTeamsList();
    }
    
    updateTeamSelection() {
        const teamCards = document.querySelectorAll('.team-selection-card');
        teamCards.forEach(card => {
            const teamId = card.dataset.teamId;
            const selectBtn = card.querySelector('.btn');
            
            if (this.selectedTeamIds.has(teamId)) {
                card.classList.add('selected');
                selectBtn.innerHTML = '<i class="icon-check"></i> Selected';
                selectBtn.classList.remove('btn-primary');
                selectBtn.classList.add('btn-success');
            } else {
                card.classList.remove('selected');
                selectBtn.innerHTML = '<i class="icon-plus"></i> Select';
                selectBtn.classList.remove('btn-success');
                selectBtn.classList.add('btn-primary');
            }
        });
        
        // Enable/disable assign button
        const assignBtn = document.getElementById('assign-teams-btn');
        if (assignBtn) {
            assignBtn.disabled = this.selectedTeamIds.size === 0;
        }
    }
    
    updateSelectedTeamsList() {
        const selectedContainer = document.getElementById('selected-team-list');
        if (!selectedContainer) return;
        
        if (this.selectedTeamIds.size === 0) {
            selectedContainer.innerHTML = '<div class="no-selection">No teams selected</div>';
            return;
        }
        
        const selectedCards = Array.from(this.selectedTeamIds).map(teamId => {
            const teamCard = document.querySelector(`[data-team-id="${teamId}"]`);
            const teamName = teamCard?.querySelector('h5')?.textContent || `Team ${teamId}`;
            
            return `
                <div class="selected-team-item">
                    <span class="team-name">${teamName}</span>
                    <button class="btn btn-sm btn-outline" onclick="operationsDashboard.selectTeam('${teamId}')">
                        <i class="icon-x"></i>
                    </button>
                </div>
            `;
        }).join('');
        
        selectedContainer.innerHTML = selectedCards;
    }
    
    async assignTeamsToOperation() {
        const operationId = document.getElementById('operation-select').value;
        const forceReassign = document.getElementById('force-reassign').checked;
        const notes = document.getElementById('assignment-notes').value;
        
        if (!operationId || this.selectedTeamIds.size === 0) {
            this.showNotification('Error', 'Please select an operation and at least one team', 'error');
            return;
        }
        
        try {
            this.showLoading('Assigning teams to operation...');
            
            const response = await fetch('/api/maritime/teams/assign', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    operation_id: operationId,
                    team_ids: Array.from(this.selectedTeamIds),
                    force: forceReassign,
                    notes: notes
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Success', 'Teams assigned successfully', 'success');
                this.closeModal('team-assignment-modal');
                this.selectedTeamIds.clear();
                
                // Refresh team performance data
                await this.refreshTeamPerformance();
            } else {
                if (response.status === 409) {
                    // Conflict - show detailed error
                    this.showTeamConflictDialog(result);
                } else {
                    throw new Error(result.error || 'Assignment failed');
                }
            }
            
        } catch (error) {
            console.error('Team assignment error:', error);
            this.showNotification('Error', error.message || 'Failed to assign teams', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    showTeamConflictDialog(conflictData) {
        const modal = document.getElementById('team-assignment-modal');
        const modalBody = modal.querySelector('.modal-body');
        
        const conflictHtml = `
            <div class="conflict-dialog">
                <h4>Team Assignment Conflicts</h4>
                <p>The following teams are already assigned to other operations:</p>
                <div class="conflict-list">
                    ${conflictData.conflicts.map(conflict => `
                        <div class="conflict-item">
                            <span class="team-name">Team ${conflict.team_id}</span>
                            <span class="conflict-details">
                                Currently assigned to ${conflict.vessel_name} (Operation ${conflict.operation_id})
                            </span>
                        </div>
                    `).join('')}
                </div>
                <p>Enable "Force reassignment" to remove these teams from their current operations.</p>
            </div>
        `;
        
        modalBody.innerHTML = conflictHtml;
    }
    
    async refreshTeamPerformance() {
        try {
            const response = await fetch('/api/maritime/teams/performance');
            const teamsData = await response.json();
            
            this.updateTeamsDisplay(teamsData);
            
            // Update summary metrics
            const summary = teamsData.overall_metrics || {};
            document.getElementById('avg-team-efficiency').textContent = 
                Math.round(summary.average_efficiency || 0) + '%';
            document.getElementById('total-throughput').textContent = 
                Math.round(summary.average_throughput || 0);
            document.getElementById('safety-incidents').textContent = 
                summary.total_safety_incidents || 0;
            document.getElementById('active-teams-count').textContent = 
                summary.active_teams || 0;
            
        } catch (error) {
            console.error('Error refreshing team performance:', error);
            this.showNotification('Error', 'Failed to refresh team performance data', 'error');
        }
    }
    
    async filterAvailableTeams() {
        const zone = document.getElementById('zone-filter-modal').value;
        const shift = document.getElementById('shift-filter-modal').value;
        const specialization = document.getElementById('specialization-filter-modal').value;
        
        // Build filter query
        const params = new URLSearchParams();
        if (zone) params.append('zone', zone);
        if (shift) params.append('shift', shift);
        if (specialization) params.append('specialization', specialization);
        
        try {
            const response = await fetch(`/api/maritime/teams/active?${params}`);
            const teamsData = await response.json();
            
            const teamsContainer = document.getElementById('available-teams');
            if (teamsContainer) {
                this.renderAvailableTeams(teamsContainer, teamsData.active_teams || []);
            }
            
        } catch (error) {
            console.error('Error filtering teams:', error);
            this.showNotification('Error', 'Failed to filter teams', 'error');
        }
    }
    
    renderAvailableTeams(container, teams) {
        if (teams.length === 0) {
            container.innerHTML = '<div class="no-teams">No teams match the selected filters</div>';
            return;
        }
        
        container.innerHTML = teams.map(team => `
            <div class="team-selection-card ${this.selectedTeamIds.has(team.id) ? 'selected' : ''}" 
                 data-team-id="${team.id}">
                <div class="team-info">
                    <h5>${team.team_name}</h5>
                    <div class="team-meta">
                        <span class="team-size">${team.team_size} members</span>
                        <span class="team-lead">${team.lead_name || 'No lead'}</span>
                        <span class="team-zone">${team.zone_assignment || 'All zones'}</span>
                    </div>
                    <div class="team-performance">
                        <div class="performance-metric">
                            <span class="metric-label">Efficiency:</span>
                            <span class="metric-value">${Math.round(team.performance?.efficiency || 0)}%</span>
                        </div>
                        <div class="performance-metric">
                            <span class="metric-label">Throughput:</span>
                            <span class="metric-value">${Math.round(team.performance?.throughput_rate || 0)} MT/h</span>
                        </div>
                    </div>
                </div>
                <div class="team-actions">
                    <button class="btn btn-sm ${this.selectedTeamIds.has(team.id) ? 'btn-success' : 'btn-primary'}" 
                            onclick="operationsDashboard.selectTeam('${team.id}')">
                        <i class="icon-${this.selectedTeamIds.has(team.id) ? 'check' : 'plus'}"></i>
                        ${this.selectedTeamIds.has(team.id) ? 'Selected' : 'Select'}
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    editTeamPerformance(teamId) {
        console.log('Editing team performance for:', teamId);
        // Open team performance edit modal
        // This would be implemented based on requirements
    }
    
    updateChart(metric) {
        // Update chart controls
        const controls = document.querySelectorAll('.chart-controls .btn');
        controls.forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
        
        // Update chart based on metric
        console.log('Updating chart for metric:', metric);
        // This would update the chart visualization
    }

    updateKPIMetrics(kpis) {
        if (!kpis) return;
        
        // Update KPI values with animation
        Object.keys(kpis).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                const oldValue = element.textContent;
                element.textContent = kpis[key];
                
                // Add flash animation for changes
                if (oldValue !== kpis[key]) {
                    element.classList.add('animate-fade-in');
                    setTimeout(() => element.classList.remove('animate-fade-in'), 300);
                }
            }
        });
    }

    updateAlertsDisplay(alerts) {
        const alertsList = document.getElementById('alerts-list');
        if (!alertsList || !alerts) return;
        
        const alertsArray = Array.isArray(alerts) ? alerts : [];
        
        if (alertsArray.length === 0) {
            alertsList.innerHTML = '<div class="no-alerts">No active alerts</div>';
            return;
        }
        
        alertsList.innerHTML = alertsArray.map(alert => this.createAlertElement(alert).outerHTML).join('');
    }

    renderBerthVesselInfo(berthElement, vesselInfo) {
        const vesselInfoSection = berthElement.querySelector('.vessel-info') || 
                                  berthElement.querySelector('.berth-empty');
        
        if (vesselInfoSection) {
            vesselInfoSection.outerHTML = `
                <div class="vessel-info">
                    <div class="vessel-name">${vesselInfo.name}</div>
                    <div class="vessel-details">
                        <span class="vessel-type">${vesselInfo.type || 'Cargo Vessel'}</span>
                        <span class="eta">Progress: ${vesselInfo.progress || 0}%</span>
                    </div>
                    <div class="operation-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${vesselInfo.progress || 0}%"></div>
                        </div>
                        <span class="progress-text">${vesselInfo.progress || 0}%</span>
                    </div>
                </div>
            `;
        }
    }

    renderEmptyBerth(berthElement) {
        const vesselInfoSection = berthElement.querySelector('.vessel-info');
        
        if (vesselInfoSection) {
            vesselInfoSection.outerHTML = `
                <div class="berth-empty">
                    <i class="icon-plus-circle"></i>
                    <span>Available</span>
                </div>
            `;
        }
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
    
    async manageBerth(berthNumber) {
        try {
            console.log('Managing berth:', berthNumber);
            
            // Get current berth status
            const response = await fetch('/maritime/berth/status');
            const berthData = await response.json();
            
            if (!response.ok) {
                throw new Error('Failed to load berth data');
            }
            
            // Find specific berth data
            const berth = berthData.berths.find(b => b.berth_number === berthNumber.toString());
            
            if (!berth) {
                throw new Error(`Berth ${berthNumber} not found`);
            }
            
            // Show berth management modal
            this.showBerthManagementModal(berth, berthData.queue);
            
        } catch (error) {
            console.error('Berth management error:', error);
            this.showNotification('Error', 'Failed to load berth management interface', 'error');
        }
    }
    
    viewTeamDetails(teamId) {
        console.log('Viewing team details:', teamId);
        // Open team details modal
    }
    
    initializeOperation() {
        console.log('Initializing new operation');
        // Navigate to maritime operations wizard step 1
        window.location.href = '/maritime/ship_operations/new/step1';
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
    console.log('Assigning vessel to berth:', vesselId);
    
    // Show berth selection modal
    operationsDashboard.showBerthSelectionModal(vesselId);
}

function showTeamAssignmentModal() {
    operationsDashboard.showTeamAssignmentModal();
}

function loadOperationDetails() {
    operationsDashboard.loadOperationDetails();
}

function filterAvailableTeams() {
    operationsDashboard.filterAvailableTeams();
}

function assignTeamsToOperation() {
    operationsDashboard.assignTeamsToOperation();
}

function refreshTeamPerformance() {
    operationsDashboard.refreshTeamPerformance();
}

function updateChart(metric) {
    operationsDashboard.updateChart(metric);
}

// TICO Vehicle Management Functions
class VehicleManager {
    constructor() {
        this.vehicles = [];
        this.currentVehicle = null;
        this.optimizationData = null;
        this.refreshInterval = null;
        this.init();
    }
    
    init() {
        console.log('Initializing Vehicle Manager');
        this.loadVehicles();
        this.setupPeriodicRefresh();
    }
    
    setupPeriodicRefresh() {
        // Refresh vehicle data every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadVehicles();
            this.updateVehicleMetrics();
        }, 30000);
    }
    
    async loadVehicles() {
        try {
            const response = await fetch('/api/maritime/vehicles/tico');
            const data = await response.json();
            
            if (response.ok) {
                this.vehicles = data.vehicles;
                this.updateVehicleDisplay();
                this.updateVehicleSummary(data);
                this.updateZoneAssignments(data.zone_summary);
            } else {
                console.error('Failed to load vehicles:', data.error);
                this.showError('Failed to load vehicles');
            }
        } catch (error) {
            console.error('Error loading vehicles:', error);
            this.showError('Error loading vehicles');
        }
    }
    
    updateVehicleDisplay() {
        const zones = ['BRV', 'ZEE', 'SOU', 'unassigned'];
        
        zones.forEach(zone => {
            const container = document.getElementById(`${zone.toLowerCase()}-vehicles`);
            if (container) {
                const zoneVehicles = this.vehicles.filter(v => 
                    zone === 'unassigned' ? !v.zone_assignment : v.zone_assignment === zone
                );
                
                container.innerHTML = this.generateVehicleCards(zoneVehicles);
            }
        });
    }
    
    generateVehicleCards(vehicles) {
        return vehicles.map(vehicle => `
            <div class="vehicle-card vehicle-${vehicle.status}" data-vehicle-id="${vehicle.id}">
                <div class="vehicle-header">
                    <div class="vehicle-license">${vehicle.license_plate}</div>
                    <div class="vehicle-status">
                        <span class="status-dot status-${vehicle.status}"></span>
                        <span class="status-text">${vehicle.status}</span>
                    </div>
                </div>
                <div class="vehicle-details">
                    <div class="detail-item">
                        <span class="label">Type:</span>
                        <span class="value">${vehicle.vehicle_type}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Capacity:</span>
                        <span class="value">${vehicle.current_load}/${vehicle.capacity}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Driver:</span>
                        <span class="value">${vehicle.driver_name || 'Unassigned'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Location:</span>
                        <span class="value">${vehicle.current_location || 'Unknown'}</span>
                    </div>
                </div>
                <div class="vehicle-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${vehicle.capacity_percentage}%"></div>
                    </div>
                    <span class="progress-text">${vehicle.capacity_percentage}% capacity</span>
                </div>
                <div class="vehicle-actions">
                    <button class="btn btn-sm btn-outline" onclick="vehicleManager.updateVehicleLocation(${vehicle.id})">
                        <i class="icon-map-pin"></i>
                        Location
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="vehicleManager.showVehicleDetails(${vehicle.id})">
                        <i class="icon-eye"></i>
                        Details
                    </button>
                    ${vehicle.is_available ? `
                        <button class="btn btn-sm btn-primary" onclick="vehicleManager.assignVehicle(${vehicle.id})">
                            <i class="icon-arrow-right"></i>
                            Assign
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }
    
    updateVehicleSummary(data) {
        const summary = data.utilization_summary || {};
        
        const totalVehiclesEl = document.getElementById('total-vehicles');
        const availableVehiclesEl = document.getElementById('available-vehicles');
        const vehicleUtilizationEl = document.getElementById('vehicle-utilization');
        const maintenanceAlertsEl = document.getElementById('maintenance-alerts');
        
        if (totalVehiclesEl) totalVehiclesEl.textContent = data.total_vehicles || 0;
        if (availableVehiclesEl) availableVehiclesEl.textContent = data.available_vehicles || 0;
        if (vehicleUtilizationEl) vehicleUtilizationEl.textContent = `${summary.average_utilization || 0}%`;
        if (maintenanceAlertsEl) maintenanceAlertsEl.textContent = '0'; // TODO: Implement maintenance alerts
        
        // Update vehicle types breakdown
        const vanCount = this.vehicles.filter(v => v.vehicle_type === 'van').length;
        const stationWagonCount = this.vehicles.filter(v => v.vehicle_type === 'station_wagon').length;
        
        const vehicleTypesEl = document.getElementById('vehicle-types');
        if (vehicleTypesEl) {
            vehicleTypesEl.innerHTML = `
                <span class="detail-item">${vanCount} Vans</span>
                <span class="detail-item">${stationWagonCount} Station Wagons</span>
            `;
        }
        
        // Update availability percentage
        const availabilityPercentage = data.total_vehicles > 0 ? 
            Math.round((data.available_vehicles / data.total_vehicles) * 100) : 0;
        
        const availabilityPercentageEl = document.getElementById('availability-percentage');
        if (availabilityPercentageEl) {
            availabilityPercentageEl.innerHTML = `
                <span class="detail-item">${availabilityPercentage}% Available</span>
            `;
        }
    }
    
    updateZoneAssignments(zoneSummary) {
        Object.keys(zoneSummary).forEach(zone => {
            const zoneData = zoneSummary[zone];
            const capacityElement = document.getElementById(`${zone.toLowerCase()}-capacity`);
            
            if (capacityElement) {
                capacityElement.textContent = `${zoneData.available_capacity || 0}/${zoneData.total_capacity || 0}`;
            }
        });
    }
    
    async assignVehicle(vehicleId) {
        this.currentVehicle = this.vehicles.find(v => v.id === vehicleId);
        if (!this.currentVehicle) return;
        
        // Populate vehicle selection modal
        const modal = document.getElementById('vehicle-assignment-modal');
        const vehicleSelect = document.getElementById('vehicle-select');
        
        if (!modal || !vehicleSelect) return;
        
        // Clear and populate vehicle options
        vehicleSelect.innerHTML = '<option value="">Select a vehicle...</option>';
        this.vehicles.filter(v => v.is_available).forEach(vehicle => {
            const option = document.createElement('option');
            option.value = vehicle.id;
            option.textContent = `${vehicle.license_plate} (${vehicle.vehicle_type})`;
            option.selected = vehicle.id === vehicleId;
            vehicleSelect.appendChild(option);
        });
        
        // Load vehicle details
        if (vehicleId) {
            this.loadVehicleDetails(vehicleId);
        }
        
        // Show modal
        modal.style.display = 'block';
    }
    
    loadVehicleDetails(vehicleId) {
        const vehicle = this.vehicles.find(v => v.id === parseInt(vehicleId));
        if (!vehicle) return;
        
        // Update vehicle details
        const elements = {
            'vehicle-license-plate': vehicle.license_plate,
            'vehicle-type': vehicle.vehicle_type,
            'vehicle-capacity': vehicle.capacity,
            'vehicle-status': vehicle.status,
            'vehicle-current-zone': vehicle.zone_assignment || 'Unassigned',
            'vehicle-available-capacity': vehicle.available_capacity
        };
        
        Object.keys(elements).forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = elements[id];
        });
        
        // Show details and assignment sections
        const detailsSection = document.getElementById('vehicle-details');
        const assignmentSection = document.getElementById('assignment-details');
        
        if (detailsSection) detailsSection.style.display = 'block';
        if (assignmentSection) assignmentSection.style.display = 'block';
        
        // Load available drivers
        this.loadAvailableDrivers();
        
        // Enable assignment button
        const assignBtn = document.getElementById('assign-vehicle-btn');
        if (assignBtn) assignBtn.disabled = false;
    }
    
    async loadAvailableDrivers() {
        try {
            const response = await fetch('/api/users');
            const data = await response.json();
            
            if (response.ok) {
                const driverSelect = document.getElementById('assignment-driver');
                if (driverSelect) {
                    driverSelect.innerHTML = '<option value="">Select driver...</option>';
                    
                    data.users.filter(user => user.role === 'worker').forEach(user => {
                        const option = document.createElement('option');
                        option.value = user.id;
                        option.textContent = `${user.first_name} ${user.last_name}`;
                        driverSelect.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading drivers:', error);
        }
    }
    
    async performVehicleAssignment() {
        const vehicleId = document.getElementById('vehicle-select').value;
        const zone = document.getElementById('assignment-zone').value;
        const driverId = document.getElementById('assignment-driver').value;
        const passengerCount = parseInt(document.getElementById('passenger-count').value);
        const location = document.getElementById('assignment-location').value;
        const coordinates = document.getElementById('assignment-coordinates').value;
        
        if (!vehicleId || !zone) {
            this.showError('Please select a vehicle and zone');
            return;
        }
        
        try {
            const response = await fetch('/api/maritime/vehicles/assign', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    vehicle_id: parseInt(vehicleId),
                    zone: zone,
                    driver_id: driverId ? parseInt(driverId) : null,
                    passenger_count: passengerCount
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Vehicle assigned successfully');
                this.closeModal('vehicle-assignment-modal');
                
                // Update location if provided
                if (location) {
                    await this.updateVehicleLocationAPI(vehicleId, location, coordinates);
                }
                
                // Refresh vehicle display
                this.loadVehicles();
            } else {
                this.showError(data.error || 'Failed to assign vehicle');
            }
        } catch (error) {
            console.error('Error assigning vehicle:', error);
            this.showError('Error assigning vehicle');
        }
    }
    
    async updateVehicleLocationAPI(vehicleId, location, coordinates) {
        try {
            const response = await fetch('/api/maritime/vehicles/update-location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    vehicle_id: parseInt(vehicleId),
                    location: location,
                    coordinates: coordinates
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Vehicle location updated');
                this.loadVehicles();
            } else {
                this.showError(data.error || 'Failed to update location');
            }
        } catch (error) {
            console.error('Error updating vehicle location:', error);
            this.showError('Error updating vehicle location');
        }
    }
    
    showVehicleDetails(vehicleId) {
        const vehicle = this.vehicles.find(v => v.id === vehicleId);
        if (!vehicle) return;
        
        // Show vehicle details in a modal or panel
        alert(`Vehicle Details:\nLicense: ${vehicle.license_plate}\nType: ${vehicle.vehicle_type}\nStatus: ${vehicle.status}\nZone: ${vehicle.zone_assignment || 'Unassigned'}`);
    }
    
    updateVehicleLocation(vehicleId) {
        const modal = document.getElementById('vehicle-location-modal');
        const vehicleSelect = document.getElementById('location-vehicle-select');
        
        if (!modal || !vehicleSelect) return;
        
        // Populate vehicle options
        vehicleSelect.innerHTML = '<option value="">Select a vehicle...</option>';
        this.vehicles.forEach(vehicle => {
            const option = document.createElement('option');
            option.value = vehicle.id;
            option.textContent = `${vehicle.license_plate} (${vehicle.vehicle_type})`;
            option.selected = vehicle.id === vehicleId;
            vehicleSelect.appendChild(option);
        });
        
        modal.style.display = 'block';
    }
    
    async performLocationUpdate() {
        const vehicleId = document.getElementById('location-vehicle-select').value;
        const location = document.getElementById('new-location').value;
        const coordinates = document.getElementById('new-coordinates').value;
        
        if (!vehicleId || !location) {
            this.showError('Please select a vehicle and enter a location');
            return;
        }
        
        await this.updateVehicleLocationAPI(vehicleId, location, coordinates);
        this.closeModal('vehicle-location-modal');
    }
    
    getCurrentLocation() {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition((position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                const coordsEl = document.getElementById('new-coordinates');
                const locationEl = document.getElementById('new-location');
                
                if (coordsEl) coordsEl.value = `${lat},${lng}`;
                if (locationEl) locationEl.value = `GPS: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
            }, (error) => {
                console.error('Error getting location:', error);
                this.showError('Unable to get current location');
            });
        } else {
            this.showError('Geolocation not supported');
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
    }
    
    showError(message) {
        console.error(message);
        // TODO: Implement proper error display
        alert(message);
    }
    
    showSuccess(message) {
        console.log(message);
        // TODO: Implement proper success display
        alert(message);
    }
    
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Global vehicle manager instance
let vehicleManager;

// Global functions for vehicle management
function showVehicleAssignmentModal() {
    if (vehicleManager) vehicleManager.assignVehicle();
}

function loadVehicleDetails() {
    const vehicleId = document.getElementById('vehicle-select').value;
    if (vehicleId && vehicleManager) {
        vehicleManager.loadVehicleDetails(vehicleId);
    }
}

function assignVehicle() {
    if (vehicleManager) vehicleManager.performVehicleAssignment();
}

function updateVehicleLocation() {
    if (vehicleManager) vehicleManager.performLocationUpdate();
}

function getCurrentLocation() {
    if (vehicleManager) vehicleManager.getCurrentLocation();
}

function optimizeZoneAssignment(zone) {
    console.log('Optimizing zone assignment for:', zone);
    // TODO: Implement zone optimization
}

function refreshVehicles() {
    if (vehicleManager) vehicleManager.loadVehicles();
}

function filterVehiclesByZone(zone) {
    console.log('Filtering vehicles by zone:', zone);
    // TODO: Implement zone filtering
}

function showVehicleTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.metric-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) selectedTab.classList.add('active');
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    if (event && event.target) {
        event.target.classList.add('active');
    }
}

function validatePassengerCount() {
    const passengerCount = parseInt(document.getElementById('passenger-count').value);
    const vehicleId = document.getElementById('vehicle-select').value;
    
    if (vehicleId && passengerCount && vehicleManager) {
        const vehicle = vehicleManager.vehicles.find(v => v.id === parseInt(vehicleId));
        if (vehicle && passengerCount > vehicle.available_capacity) {
            vehicleManager.showError(`Passenger count exceeds available capacity (${vehicle.available_capacity})`);
            document.getElementById('passenger-count').value = vehicle.available_capacity;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.operationsDashboard = new OperationsDashboard();
    vehicleManager = new VehicleManager();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OperationsDashboard, VehicleManager };
}