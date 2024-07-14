// portfolio-review.js

// Function to handle form submission
document.getElementById('reviewForm').addEventListener('submit', async function (event) {
    event.preventDefault(); // Prevent the default form submission

    // Show the loader
    document.getElementById('loader').style.display = 'block';

    // Disable all buttons except navigation buttons
    var allButtons = document.querySelectorAll('button');
    allButtons.forEach(function (button) {
        if (!button.classList.contains('navbar-toggler')) {
            button.disabled = true;
        }
    });

    // Disable form submit button
    var submitButton = document.querySelector('form button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
    }

    // Disable links inside icon spans
    var iconLinks = document.querySelectorAll('li > a, a');
    iconLinks.forEach(function (iconLink) {
        iconLink.style.pointerEvents = 'none';
        iconLink.style.opacity = '0.5';
    });

    // Collect form data
    var formData = new FormData(event.target);

    // Use Fetch API to submit the form data
    try {
        const response = await fetch(event.target.action, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            console.log('Response status:', response.status);
            const text = await response.text();
            throw new Error(text);
        }

        if (response.headers.get('content-type')?.includes('application/json')) {
            const data = await response.json();
            console.log('Data received:', data);

            // Hide the loader
            document.getElementById('loader').style.display = 'none';

            // Enable buttons and links
            allButtons.forEach(function (button) {
                if (!button.classList.contains('navbar-toggler')) {
                    button.disabled = false;
                }
            });
            if (submitButton) {
                submitButton.disabled = false;
            }
            iconLinks.forEach(function (iconLink) {
                iconLink.style.pointerEvents = 'auto';
                iconLink.style.opacity = '1';
            });

            // Display the result or perform any other actions based on the response
            if (data.website_review) {
                document.getElementById('reviewResult').innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="md:col-span-1">
                        <h3 class="text-lg white font-bold">Portfolio Feedback:</h3>
                        <textarea readonly class="textarea_details textarea-memory w-full p-2 border border-gray-300" style="min-height: 991px;">${data.website_review}</textarea>
                    </div>
                </div>    
                `;

                var audioSource = document.getElementById('audioSource');
                audioSource.src = data.tts_url;
                var audioElement = document.getElementById('audioElement');
                audioElement.load(); // Reload the audio element to apply the new source

                document.getElementById('updateLike').classList.remove('hidden');
                document.getElementById('reviewResult').classList.remove('hidden');
                document.getElementById('rating_section').classList.remove('hidden');
                document.getElementById('audioFeedback').classList.remove('hidden');
            }
            if (data.website_screenshot) {
                document.getElementById('screenshotResult').innerHTML = `
                <h3 class="text-lg font-bold">Website Screenshot:</h3>
                <img src="${data.website_screenshot}" alt="Website Screenshot" class="mt-2" style="width: 100%; height: auto;" />
                `;
                document.getElementById('screenshotResult').classList.remove('hidden');
            }
        } else {
            throw new Error('Unexpected response type');
        }
    } catch (error) {
        console.error('There has been a problem with your fetch operation:', error);

        // Hide the loader and enable the buttons if needed
        document.getElementById('loader').style.display = 'none';
        allButtons.forEach(function (button) {
            if (!button.classList.contains('navbar-toggler')) {
                button.disabled = false;
            }
        });
        if (submitButton) {
            submitButton.disabled = false;
        }
        iconLinks.forEach(function (iconLink) {
            iconLink.style.pointerEvents = 'auto';
            iconLink.style.opacity = '1';
        });

        // Handle specific error conditions
        if (error.message.includes('Unexpected token')) {
            alert('There was an error processing your request. Please try again later.');
        } else {
            alert('There was a problem with your request. Please try again later.');
        }
    }
});

// Function to handle rate feedback
function rateFeedback(review_id, rating) {
    fetch(`/feedback`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ review_id: review_id, rating: rating }),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Update UI to reflect the new rating
                alert('Feedback submitted successfully!');
                var ratingElement = document.querySelector(`.rating[data-review-id="${review_id}"]`);
                if (ratingElement) {
                    ratingElement.innerText = `Rating: ${rating}`;
                }
            } else {
                console.error('Failed to submit rating');
                alert('Failed to submit feedback. Please try again.');
            }
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
            alert('There was a problem with your request. Please try again later.');
        });
}

// Function to toggle like status
function toggleLike(reviewId, liked) {
    fetch(`/like/${reviewId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ liked: liked }),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Updated like successfully!');
                // Update UI to reflect the new like status
                var likeButton = document.querySelector(`.icon-circle[data-review-id="${reviewId}"]`);
                if (likeButton) {
                    likeButton.classList.toggle('liked', liked);
                }
            } else {
                console.error('Failed to toggle like status');
                alert('Failed to toggle like status. Please try again.');
            }
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
            alert('There was a problem with your request. Please try again later.');
        });
}

function scrollDown() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}
