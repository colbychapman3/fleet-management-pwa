// Service Worker template - this will be served with proper headers
// Content is the same as /static/js/sw.js but served through Flask template system

{{ url_for('static', filename='js/sw.js') }}

// This template serves the service worker file with proper MIME type and headers
// The actual service worker code is in /static/js/sw.js