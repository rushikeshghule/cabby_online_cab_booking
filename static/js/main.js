// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Handle file input display
document.addEventListener('DOMContentLoaded', function() {
    const fileInputs = document.querySelectorAll('.custom-file-input');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0].name;
            const label = e.target.nextElementSibling;
            label.textContent = fileName;
        });
    });
});

// Rating stars functionality
function initRatingStars() {
    const ratingContainers = document.querySelectorAll('.rating-container');
    ratingContainers.forEach(container => {
        const stars = container.querySelectorAll('.rating-star');
        const input = container.querySelector('input[type="hidden"]');
        
        stars.forEach((star, index) => {
            star.addEventListener('click', () => {
                const rating = index + 1;
                input.value = rating;
                updateStars(stars, rating);
            });
            
            star.addEventListener('mouseover', () => {
                updateStars(stars, index + 1);
            });
            
            star.addEventListener('mouseout', () => {
                updateStars(stars, input.value);
            });
        });
    });
}

function updateStars(stars, rating) {
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

// WebSocket connection for chat
function initWebSocket(rideId) {
    const chatSocket = new WebSocket(
        'ws://' + window.location.host + '/ws/chat/' + rideId + '/'
    );

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        appendMessage(data.message, data.sender_id === currentUserId);
    };

    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
    };

    return chatSocket;
}

function appendMessage(message, isSent) {
    const chatContainer = document.querySelector('.chat-container');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message');
    messageDiv.classList.add(isSent ? 'sent' : 'received');
    messageDiv.textContent = message;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Google Maps initialization
function initMap(mapContainer, initialLocation = { lat: -34.397, lng: 150.644 }) {
    const map = new google.maps.Map(mapContainer, {
        zoom: 14,
        center: initialLocation,
    });
    return map;
}

// Get current location
function getCurrentLocation(callback) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const location = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                callback(null, location);
            },
            (error) => {
                callback(error);
            }
        );
    } else {
        callback(new Error('Geolocation is not supported by this browser.'));
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Export functions for use in other scripts
window.cabby = {
    initRatingStars,
    initWebSocket,
    initMap,
    getCurrentLocation,
    formatCurrency,
    formatDate
}; 