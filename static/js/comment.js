// comment.js
document.getElementById('comment-form').addEventListener('submit', function(event) {
    event.preventDefault();  // Prevent the default form submission

    let formData = new FormData(this);  // Collect form data

    fetch(this.action, {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        const notification = document.getElementById('notification');

        // Create a notification div
        const notificationDiv = document.createElement('div');
        notificationDiv.classList.add('alert');

        // Set notification message based on the response
        if (data.status === 'success') {
            notificationDiv.classList.add('alert-success');
            notificationDiv.innerText = data.message;
        } else {
            notificationDiv.classList.add('alert-danger');
            notificationDiv.innerText = data.message;
        }

        // Append the notification to the notification container
        notification.appendChild(notificationDiv);

        // Clear the form and possibly reload comments
        if (data.status === 'success') {
            document.getElementById('comment-form').reset();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
