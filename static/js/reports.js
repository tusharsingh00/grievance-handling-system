// Enhanced Reports JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts with animations
    initializeCharts();
    
    // Add 3D tilt effect to cards
    const cards = document.querySelectorAll('.card-3d');
    cards.forEach(card => {
        card.addEventListener('mousemove', handleTilt);
        card.addEventListener('mouseleave', resetTilt);
    });
});

function handleTilt(e) {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    const rotateX = (y - centerY) / 10;
    const rotateY = -(x - centerX) / 10;
    
    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
}

function resetTilt(e) {
    const card = e.currentTarget;
    card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
}

function initializeCharts() {
    // Category Distribution Chart
    new Chart(document.getElementById('categoryChart'), {
        type: 'doughnut',
        data: categoryData,
        options: {
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.label}: ${context.parsed}%`
                    }
                }
            },
            animation: {
                animateScale: true,
                animateRotate: true,
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });

    // Monthly Trend Chart
    new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: trendData,
        options: {
            plugins: {
                legend: { display: false }
            },
            animation: {
                tension: {
                    duration: 2000,
                    easing: 'easeInOutQuart',
                    from: 1,
                    to: 0
                }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // Status Distribution Chart
    new Chart(document.getElementById('statusChart'), {
        type: 'polarArea',
        data: statusData,
        options: {
            plugins: {
                legend: { position: 'right' }
            },
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
    });

    // Priority Distribution Chart
    new Chart(document.getElementById('priorityChart'), {
        type: 'radar',
        data: priorityData,
        options: {
            elements: {
                line: { borderWidth: 3 }
            },
            animation: {
                duration: 2000
            }
        }
    });
}

// Update notification badge
function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        badge.textContent = count;
        badge.classList.add('pulse');
        setTimeout(() => badge.classList.remove('pulse'), 1000);
    }
}

// Handle feedback submission
function handleFeedbackSubmission(grievanceId) {
    const form = document.getElementById(`feedback-form-${grievanceId}`);
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/submit-feedback/', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                showNotification('Feedback submitted successfully', 'success');
                updateDashboard();
            }
        } catch (error) {
            showNotification('Error submitting feedback', 'error');
        }
    });
}

// Show animated notification
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} slide-in`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.classList.add('slide-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}