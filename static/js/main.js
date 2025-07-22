// Main JavaScript for Fleet Management PWA
(function() {
    'use strict';

    // Initialize the application
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Fleet Management PWA loaded');
        
        // Initialize service worker
        if ('serviceWorker' in navigator) {
            initServiceWorker();
        }
        
        // Initialize UI components
        initComponents();
        
        // Initialize offline handling
        initOfflineHandling();
        
        // Initialize notifications
        initNotifications();
    });

    // Service Worker registration
    function initServiceWorker() {
        navigator.serviceWorker.register('/service-worker.js')
            .then(function(registration) {
                console.log('Service Worker registered successfully:', registration);
                
                // Check for updates
                registration.addEventListener('updatefound', function() {
                    console.log('Service Worker update found');
                    const newWorker = registration.installing;
                    
                    newWorker.addEventListener('statechange', function() {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch(function(error) {
                console.log('Service Worker registration failed:', error);
            });
    }

    // Initialize UI components
    function initComponents() {
        // Mobile menu toggle
        const mobileMenuToggle = document.querySelector('[data-mobile-menu-toggle]');
        const mobileMenu = document.querySelector('[data-mobile-menu]');
        
        if (mobileMenuToggle && mobileMenu) {
            mobileMenuToggle.addEventListener('click', function() {
                mobileMenu.classList.toggle('hidden');
            });
        }
        
        // Modal handling
        initModals();
        
        // Form validation
        initFormValidation();
        
        // Toast notifications
        initToasts();
        
        // Auto-refresh for dashboard pages
        if (window.location.pathname.includes('dashboard')) {
            initDashboardRefresh();
        }
    }

    // Modal initialization
    function initModals() {
        const modalTriggers = document.querySelectorAll('[data-modal-trigger]');
        const modalCloses = document.querySelectorAll('[data-modal-close]');
        
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', function() {
                const modalId = this.getAttribute('data-modal-trigger');
                const modal = document.getElementById(modalId);
                if (modal) {
                    modal.classList.remove('hidden');
                    document.body.style.overflow = 'hidden';
                }
            });
        });
        
        modalCloses.forEach(close => {
            close.addEventListener('click', function() {
                const modal = this.closest('[data-modal]');
                if (modal) {
                    modal.classList.add('hidden');
                    document.body.style.overflow = '';
                }
            });
        });
        
        // Close modal on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('[data-modal]:not(.hidden)');
                if (openModal) {
                    openModal.classList.add('hidden');
                    document.body.style.overflow = '';
                }
            }
        });
    }

    // Form validation
    function initFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!validateForm(this)) {
                    e.preventDefault();
                }
            });
        });
    }

    function validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                showFieldError(field, 'This field is required');
                isValid = false;
            } else {
                clearFieldError(field);
            }
        });
        
        return isValid;
    }

    function showFieldError(field, message) {
        clearFieldError(field);
        field.classList.add('border-red-500');
        
        const error = document.createElement('div');
        error.className = 'text-red-500 text-sm mt-1';
        error.textContent = message;
        error.setAttribute('data-field-error', '');
        
        field.parentNode.insertBefore(error, field.nextSibling);
    }

    function clearFieldError(field) {
        field.classList.remove('border-red-500');
        const error = field.parentNode.querySelector('[data-field-error]');
        if (error) {
            error.remove();
        }
    }

    // Toast notifications
    function initToasts() {
        window.showToast = function(message, type = 'info', duration = 5000) {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type} fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300`;
            
            const colorMap = {
                success: 'bg-green-500 text-white',
                error: 'bg-red-500 text-white',
                warning: 'bg-yellow-500 text-black',
                info: 'bg-blue-500 text-white'
            };
            
            toast.className += ' ' + (colorMap[type] || colorMap.info);
            toast.textContent = message;
            
            document.body.appendChild(toast);
            
            // Animate in
            setTimeout(() => {
                toast.classList.remove('translate-x-full');
            }, 100);
            
            // Auto remove
            setTimeout(() => {
                toast.classList.add('translate-x-full');
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }, duration);
            
            // Click to dismiss
            toast.addEventListener('click', () => {
                toast.classList.add('translate-x-full');
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            });
        };
    }

    // Offline handling
    function initOfflineHandling() {
        window.addEventListener('online', function() {
            console.log('Connection restored');
            showToast('Connection restored', 'success');
            
            // Sync pending data
            if (window.syncManager) {
                window.syncManager.syncPendingData();
            }
        });
        
        window.addEventListener('offline', function() {
            console.log('Connection lost');
            showToast('Working offline', 'warning');
        });
    }

    // Notifications
    function initNotifications() {
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        window.showNotification = function(title, options = {}) {
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(title, {
                    icon: '/static/icons/icon-192x192.png',
                    badge: '/static/icons/icon-72x72.png',
                    ...options
                });
            }
        };
    }

    // Dashboard auto-refresh
    function initDashboardRefresh() {
        // Refresh dashboard data every 30 seconds
        const refreshInterval = 30000; // 30 seconds
        
        setInterval(function() {
            if (document.visibilityState === 'visible') {
                refreshDashboardData();
            }
        }, refreshInterval);
        
        // Refresh when page becomes visible
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') {
                refreshDashboardData();
            }
        });
    }

    function refreshDashboardData() {
        // Only refresh if no modals are open
        const openModal = document.querySelector('[data-modal]:not(.hidden)');
        if (openModal) return;
        
        // Refresh specific dashboard components
        const refreshableElements = document.querySelectorAll('[data-auto-refresh]');
        
        refreshableElements.forEach(element => {
            const url = element.getAttribute('data-refresh-url');
            if (url) {
                fetch(url)
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const newElement = doc.querySelector(`[data-auto-refresh="${element.getAttribute('data-auto-refresh')}"]`);
                        
                        if (newElement) {
                            element.innerHTML = newElement.innerHTML;
                        }
                    })
                    .catch(error => {
                        console.log('Refresh failed:', error);
                    });
            }
        });
    }

    // Service Worker update notification
    function showUpdateNotification() {
        const updateBanner = document.createElement('div');
        updateBanner.className = 'fixed top-0 left-0 right-0 bg-blue-600 text-white p-3 text-center z-50';
        updateBanner.innerHTML = `
            <span>A new version is available!</span>
            <button onclick="window.location.reload()" class="ml-4 bg-white text-blue-600 px-3 py-1 rounded text-sm">
                Update Now
            </button>
            <button onclick="this.parentNode.remove()" class="ml-2 text-white hover:text-gray-200">
                ×
            </button>
        `;
        
        document.body.insertBefore(updateBanner, document.body.firstChild);
    }

    // Utility functions
    window.FleetUtils = {
        formatDate: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        },
        
        formatCurrency: function(amount) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount);
        },
        
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    };

})();