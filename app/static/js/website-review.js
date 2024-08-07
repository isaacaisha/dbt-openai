// WEBSITE-REVIEW.JS

let audio = null;

// Function to fetch TTS URL and play audio
async function fetchTtsUrl(reviewId) {
    try {
        const response = await fetch(`/review/${reviewId}/tts-url`);
        const data = await response.json();
        if (response.ok) {
            const ttsUrl = data.tts_url;
            if (ttsUrl) {
                console.log(`TTS URL found: ${ttsUrl}`);
                initializeAudio(ttsUrl);
            } else {
                console.error('No TTS URL found in response');
            }
        } else {
            console.error(`Error fetching TTS URL: ${data.error}`);
        }
    } catch (error) {
        console.error(`Fetch error: ${error}`);
    }
}

// Function to initialize audio and set up button event handlers
function initializeAudio(ttsUrl) {
    if (audio) {
        audio.pause(); // Stop any previously playing audio
    }

    audio = new Audio(ttsUrl);

    // Handle play button click
    document.getElementById('playButton').addEventListener('click', () => {
        if (audio) {
            audio.play().catch(error => console.error(`Audio play error: ${error}`));
            document.getElementById('playButton').disabled = true;
            document.getElementById('pauseButton').disabled = false;
        }
    });

    // Handle pause button click
    document.getElementById('pauseButton').addEventListener('click', () => {
        if (audio) {
            audio.pause();
            document.getElementById('playButton').disabled = false;
            document.getElementById('pauseButton').disabled = true;
        }
    });

    // Ensure the pause button is disabled initially
    document.getElementById('pauseButton').disabled = true;
}

document.addEventListener('DOMContentLoaded', function () {
    // Function to handle form submission
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.addEventListener('submit', async function (event) {
            event.preventDefault(); // Prevent the default form submission

            // Show the loader
            document.getElementById('loader').style.display = 'block';

            // Disable the submit button
            const submitButton = document.querySelector('#reviewForm input[type="submit"]');
            submitButton.disabled = true;

            // Disable all buttons
            disableAllButtons(true);

            // Collect form data
            const formData = new FormData(event.target);

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

                    // Enable submit button and links
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
    }
});

// Function to disable/enable all buttons and links
function disableAllButtons(disable) {
    const allButtons = document.querySelectorAll('button');
    allButtons.forEach(button => button.disabled = disable);

    const iconLinks = document.querySelectorAll('li > a, a');
    iconLinks.forEach(iconLink => {
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
            // Call fetchTtsUrl instead of directly setting the audio source
            fetchTtsUrl(data.review_id);
        }

        document.getElementById('updateLike').classList.remove('hidden');
        document.getElementById('reviewResult').classList.remove('hidden');
        document.getElementById('audioFeedback').classList.remove('hidden');
        document.getElementById('rating_section').classList.remove('hidden');
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
async function rateFeedback(id, user_rating) {
    console.log("rateFeedback called with review_id:", id, "and user_rating:", user_rating);

    if (!id) {
        console.error("No id provided");
        alert('Review ID is missing.');
        return;
    }

    try {
        const response = await fetch('/rate-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id, user_rating }),
        });

        const data = await response.json();
        console.log("Response from server:", data);

        const feedbackMessage = document.getElementById("feedbackMessage");

        if (response.ok) {
            feedbackMessage.textContent = 'Thanks for Your Feedback!';
            feedbackMessage.classList.remove('hidden');
        } else {
            feedbackMessage.textContent = 'Failed to rate feedback.';
            feedbackMessage.classList.remove('hidden');
        }

        // Hide the message after 2 seconds
        setTimeout(() => {
            feedbackMessage.classList.add('hidden');
        }, 2000);

    } catch (error) {
        console.error('Error:', error);
        const feedbackMessage = document.getElementById("feedbackMessage");
        feedbackMessage.textContent = 'Error rating feedback.';
        feedbackMessage.classList.remove('hidden');

        // Hide the message after 2 seconds
        setTimeout(() => {
            feedbackMessage.classList.add('hidden');
        }, 2000);
    }
}

// Function to toggle like status
function toggleLike(review_id) {
    const likeIcon = document.querySelector(`#likeIcon${review_id}`);
    const likeMessage = document.querySelector(`#likeMessage${review_id}`);
    const unlikeMessage = document.querySelector(`#unlikeMessage${review_id}`);

    fetch(`/like/${review_id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ liked: !likeIcon.classList.contains('liked') }) // Toggle liked status
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.liked) {
                    likeIcon.classList.add('liked');
                    likeIcon.style.color = 'pink';
                    likeMessage.classList.remove('hidden');
                    unlikeMessage.classList.add('hidden');
                } else {
                    likeIcon.classList.remove('liked');
                    likeIcon.style.color = '';
                    likeMessage.classList.add('hidden');
                    unlikeMessage.classList.remove('hidden');
                }
                setTimeout(() => {
                    likeMessage.classList.add('hidden');
                    unlikeMessage.classList.add('hidden');
                }, 2000); // Hide the message after 2 seconds
                console.log('Like status updated successfully');
            } else {
                console.error(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Function to scroll down the page
function scrollDown() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}
