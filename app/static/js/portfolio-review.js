// portfolio-review.js

document.getElementById('reviewForm').addEventListener('submit', function (event) {
    // Show the loader
    document.getElementById('loader').style.display = 'block';

    // Disable all buttons except navigation buttons
    var allButtons = document.querySelectorAll('button');
    allButtons.forEach(function (button) {
        if (!button.classList.contains('nav-link')) {
            button.disabled = true;
        }
    });

    // Disable form submit button
    var submitButton = document.querySelector('form button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
    }

    // Disable links inside icon spans
    var iconLinks = document.querySelectorAll('a span.fa-stack');
    iconLinks.forEach(function (iconLink) {
        iconLink.style.pointerEvents = 'none';
        iconLink.style.opacity = '0.5';
    });
});

function rateFeedback(rating) {
    const conversationId = document.querySelector('.like-button').dataset.conversationId;

    fetch('/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ conversation_id: conversationId, type: rating })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Feedback submitted successfully!');
                // Optionally, update UI or perform any additional actions
            } else {
                alert('Failed to submit feedback. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while submitting feedback.');
        });
}

document.querySelector('.like-button').addEventListener('click', function () {
    const conversationId = this.dataset.conversationId;

    fetch('/update_like/${conversationId}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ liked: true })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.style.color = 'pink';
                document.getElementById("likeMessage").style.display = "block";
                setTimeout(function () {
                    document.getElementById("likeMessage").style.display = "none";
                }, 2000);
            }
        })
        .catch(error => console.error('Error:', error));
});

function scrollDown() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}
