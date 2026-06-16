// Priority Information tooltips
const priorityInfo = {
    'low': 'Resolution within 72 hours',
    'medium': 'Resolution within 48 hours',
    'high': 'Resolution within 24 hours',
    'urgent': 'Resolution within 12 hours',
    'critical': 'Resolution within 6 hours'
};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize priority select tooltips
    const prioritySelect = document.querySelector('.priority-select');
    if (prioritySelect) {
        prioritySelect.addEventListener('change', function() {
            updatePriorityInfo(this.value);
        });
        // Initialize tooltip for current value
        updatePriorityInfo(prioritySelect.value);
    }

    // Initialize status update form
    const statusForm = document.getElementById('status-update-form');
    if (statusForm) {
        statusForm.addEventListener('submit', handleStatusUpdate);
    }

    // Initialize comment form
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', handleCommentSubmit);
    }

    // Initialize file upload preview
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', handleFilePreview);
    }
});

function updatePriorityInfo(priority) {
    const infoElement = document.getElementById('priority-info');
    if (infoElement && priorityInfo[priority]) {
        infoElement.textContent = priorityInfo[priority];
    }
}

async function handleStatusUpdate(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            const result = await response.json();
            showNotification('Status updated successfully', 'success');
            updateStatusDisplay(result.new_status);
        } else {
            showNotification('Error updating status', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error updating status', 'error');
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.notifications').appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function handleFilePreview(event) {
    const file = event.target.files[0];
    const preview = document.getElementById('file-preview');
    
    if (preview && file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (file.type.startsWith('image/')) {
                preview.innerHTML = `<img src="${e.target.result}" class="img-thumbnail" alt="Preview">`;
            } else {
                preview.innerHTML = `<div class="file-preview-box">
                    <i class="bi bi-file-earmark"></i>
                    <span>${file.name}</span>
                </div>`;
            }
        };
        reader.readAsDataURL(file);
    }
}