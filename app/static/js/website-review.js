// portfolio-review.js

// Function to handle form submission
document.getElementById('reviewForm').addEventListener('submit', async function (event) {
    event.preventDefault(); // Prevent the default form submission

    // Show the loader
    document.getElementById('loader').style.display = 'block';

    // Disable the submit button
    const submitButton = document.querySelector('#reviewForm input[type="submit"]');
    submitButton.disabled = true;
    
    // Disable all buttons except navigation buttons
    disableAllButtons(true);

    // Collect form data
    var formData = new FormData(event.target);

    // Use Fetch API to submit the form data
    try {
        const response = await fetch(event.target.action, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        if (response.headers.get('content-type')?.includes('application/json')) {
            const data = await response.json();
            console.log('Data received:', data);

            // Hide the loader
            document.getElementById('loader').style.display = 'none';

            // Enable submitButton buttons and links
            submitButton.disabled = false;
            disableAllButtons(false);

            // Display the result or perform any other actions based on the response
            displayReviewResult(data);

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
        handleError(error);
    }
});

// Function to disable/enable all buttons and links
function disableAllButtons(disable) {
    var allButtons = document.querySelectorAll('button');
    allButtons.forEach(function (button) {
        if (!button.classList.contains('navbar-toggler')) {
            button.disabled = disable;
        }
    });

    var iconLinks = document.querySelectorAll('li > a, a');
    iconLinks.forEach(function (iconLink) {
        iconLink.style.pointerEvents = disable ? 'none' : 'auto';
        iconLink.style.opacity = disable ? '0.5' : '1';
    });
}

// Function to display review result
function displayReviewResult(data) {
    if (data.website_review) {
        document.getElementById('reviewResult').innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="md:col-span-1">
                    <h3 class="text-lg white font-bold">Website Feedback:</h3>
                    <textarea readonly class="textarea_details textarea-memory w-full p-2 border border-gray-300" style="min-height: 991px;">${data.website_review}</textarea>
                </div>
            </div>
        `;

        if (data.tts_url) {
            var audioSource = document.getElementById('audioSource');
            audioSource.src = data.tts_url;
            var audioElement = document.getElementById('audioElement');
            audioElement.load();
        }

        document.getElementById('updateLike').classList.remove('hidden');
        document.getElementById('reviewResult').classList.remove('hidden');
        document.getElementById('rating_section').classList.remove('hidden');
        document.getElementById('audioFeedback').classList.remove('hidden');
    }
}

// Function to handle errors
function handleError(error) {
    console.error('There has been a problem with your fetch operation:', error);

    // Hide the loader and enable the buttons if needed
    document.getElementById('loader').style.display = 'none';
    disableAllButtons(false);

    // Handle specific error conditions
    if (error.message.includes('Unexpected token')) {
        alert('There was an error processing your request. Please try again later.');
    } else {
        alert('There was a problem with your request. Please try again later.');
    }
}

// Function to handle rate feedback
function rateFeedback(review_id, rating) {
    fetch(`/feedback`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: review_id, user_rating: rating }),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                alert('Feedback submitted successfully!');
            } else {
                alert('Failed to submit feedback. Please try again.');
            }
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
            alert('There was a problem with your request. Please try again later.');
        });
}
        // .then(data => {
        //     if (data.status === 'success') {
        //         alert('Feedback submitted successfully!');
        //         var ratingElement = document.querySelector(`.rating[data-review-id="${review_id}"]`);
        //         if (ratingElement) {
        //             ratingElement.innerText = `Rating: ${rating}`;
        //         }
        //     } else {
        //         alert('Failed to submit feedback. Please try again.');
        //     }
        // })
        // .catch(error => {
        //     console.error('There has been a problem with your fetch operation:', error);
        //     alert('There was a problem with your request. Please try again later.');
        // });
// }

// Function to toggle like status
function toggleLike(reviewId) {
    fetch(`/like/${reviewId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error(data.error);
                return;
            }
            const likeIcon = document.querySelector(`#likeIcon${reviewId}`);
            if (data.liked) {
                likeIcon.classList.add('liked');
            } else {
                likeIcon.classList.remove('liked');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

//JavaScript for scrolling down 
function scrollDown() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}
