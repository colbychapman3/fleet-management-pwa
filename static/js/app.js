document.addEventListener('DOMContentLoaded', function() {
    // User menu dropdown functionality
    const userMenuToggle = document.getElementById('user-menu-toggle');
    const userMenuDropdown = document.getElementById('user-menu-dropdown');

    if (userMenuToggle && userMenuDropdown) {
        userMenuToggle.addEventListener('click', function() {
            userMenuDropdown.classList.toggle('show');
        });

        // Close the dropdown if the user clicks outside of it
        window.addEventListener('click', function(event) {
            if (!userMenuToggle.contains(event.target) && !userMenuDropdown.contains(event.target)) {
                userMenuDropdown.classList.remove('show');
            }
        });
    }

    // Flash message dismiss functionality
    const flashCloseButtons = document.querySelectorAll('.flash-close');
    flashCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });

    // Basic connectivity status (can be enhanced with service worker events)
    const connectivityBar = document.getElementById('connectivity-bar');
    const connectionStatus = document.getElementById('connection-status');
    const connectivityIndicator = document.getElementById('connectivity-indicator');

    function updateConnectivityStatus() {
        if (navigator.onLine) {
            connectivityBar.classList.remove('offline');
            connectivityIndicator.classList.remove('offline');
            connectionStatus.textContent = 'Online';
            connectivityBar.classList.add('hidden'); // Hide if online
        } else {
            connectivityBar.classList.add('offline');
            connectivityIndicator.classList.add('offline');
            connectionStatus.textContent = 'Offline';
            connectivityBar.classList.remove('hidden'); // Show if offline
        }
    }

    window.addEventListener('online', updateConnectivityStatus);
    window.addEventListener('offline', updateConnectivityStatus);
    updateConnectivityStatus(); // Initial check

    // Sync status (placeholder, actual sync logic in sw.js and sync.js)
    const syncStatusElement = document.getElementById('sync-status');
    const syncIndicator = document.getElementById('sync-indicator');
    const syncMessage = document.getElementById('sync-message');

    // Example of how to update sync status (this would be triggered by sync events)
    function setSyncStatus(status) {
        if (status === 'syncing') {
            syncIndicator.classList.add('syncing');
            syncMessage.textContent = 'Syncing...';
            syncStatusElement.classList.remove('hidden');
        } else if (status === 'synced') {
            syncIndicator.classList.remove('syncing');
            syncMessage.textContent = 'Synced';
            syncStatusElement.classList.add('hidden'); // Hide when synced
        } else if (status === 'failed') {
            syncIndicator.classList.remove('syncing');
            syncIndicator.style.backgroundColor = 'var(--error-color)';
            syncMessage.textContent = 'Sync Failed!';
            syncStatusElement.classList.remove('hidden');
        }
    }

    // For demonstration:
    // setSyncStatus('syncing');
    // setTimeout(() => setSyncStatus('synced'), 3000);
});
