//INTERFACE-SPEECH-REQUEST.JS

// Function to get the CSRF token from cookies
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

// Function to send a POST request to the server
function sendRequest(prompt) {
    const csrfToken = getCookie('csrf_token');
    // Show loading indicator
    showLoading();

    // Disable buttons
    const buttons = ['speechRecognitionButton', 'generateButton', 'playbackButton', 'start-button'];
    buttons.forEach(id => document.getElementById(id).disabled = true);

    // Disable all buttons except navigation buttons
    disableAllButtons(true);
    interruptButton.disabled = false;

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/interface/answer', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.setRequestHeader('X-CSRFToken', csrfToken);

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            hideLoading();
            buttons.forEach(id => document.getElementById(id).disabled = false);
            disableAllButtons(false);

            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);

                // Display the text response in the textarea
                const textarea = document.getElementById('generatedText');
                textarea.value = response.answer_text;

                // Store the detected language as a data attribute
                textarea.dataset.detectedLang = response.detected_lang || 'es-ES';
                textarea.style.display = response.answer_text ? 'block' : 'none';

                // Display the audio and playback button
                document.getElementById('response-audio').style.display = 'block';
                document.getElementById('playbackButtonContainer').style.display = 'block';

                if (response.answer_text) {
                    smoothScrollToBottomWhileTyping(response.answer_text);

                    // Use the SpeechSynthesis API to read the response aloud
                    const speech = new SpeechSynthesisUtterance(response.answer_text);
                    speech.lang = response.detected_lang || 'es-ES';
                    speech.onend = () => interruptButton.style.display = 'none';
                    speech.onboundary = event => {
                        if (event.name === 'word') {
                            smoothScrollToBottom();
                        }
                    };
                    window.speechSynthesis.speak(speech);
                }

                // Update the audio source
                updateAudioSource();

                // Ensure the stop button remains visible during speech synthesis
                interruptButton.style.display = 'block';
            } else {
                interruptButton.style.display = 'none'; // Hide the interrupt button if request fails
                console.error('Request failed:', xhr.status, xhr.statusText);
            }
        }
    };

    xhr.onerror = function () {
        hideLoading();
        buttons.forEach(id => document.getElementById(id).disabled = false);
        disableAllButtons(false);
        console.error('Network error'); // Handle network errors
    };

    xhr.send('prompt=' + encodeURIComponent(prompt));
}

// Function to update the audio source
function updateAudioSource() {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/latest-audio-url', true);

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            if (response.audio_url) {
                const audio = document.getElementById('response-audio');
                const source = audio.querySelector('source');
                source.src = response.audio_url;

                // Load and play the new audio
                audio.load();
                // Optionally, you can automatically play the audio here
                //audio.play();
            }
        }
    };

    xhr.send();
}

// Function to disable/enable all buttons and links
function disableAllButtons(disable) {
    var allButtons = document.querySelectorAll('button');
    allButtons.forEach(function (button) {
        button.disabled = disable;
    });

    var iconLinks = document.querySelectorAll('li > a, a');
    iconLinks.forEach(function (iconLink) {
        iconLink.style.pointerEvents = disable ? 'none' : 'auto';
        iconLink.style.opacity = disable ? '0.5' : '1';
    });
}

// Function to show the loading indicator
function showLoading() {
    var loadingIndicator = document.getElementById('loading-indicator');
    loadingIndicator.style.display = 'block';
}

// Function to hide the loading indicator
function hideLoading() {
    var loadingIndicator = document.getElementById('loading-indicator');
    loadingIndicator.style.display = 'none';
}

// Function to smoothly scroll the textarea to the bottom
function smoothScrollToBottom() {
    var textarea = document.getElementById('generatedText');
    var start = textarea.scrollTop;
    var end = textarea.scrollHeight;
    var change = end - start;
    var duration = 1000; // Duration for scrolling
    var startTime = performance.now();

    function scroll(timestamp) {
        var elapsed = timestamp - startTime;
        var progress = Math.min(elapsed / duration, 1);
        textarea.scrollTop = start + (change * progress);
        if (progress < 1) {
            requestAnimationFrame(scroll);
        }
    }

    requestAnimationFrame(scroll);
}

// Function to scroll gradually while text is being typed
function smoothScrollToBottomWhileTyping(text) {
    var textarea = document.getElementById('generatedText');
    textarea.value = ''; // Clear the textarea before typing starts

    var index = 0;
    var typingSpeed = 57; // Adjust this value to control typing speed
    typingInProgress = true; // Set the typing flag to true

    function typeText() {
        if (!typingInProgress) return; // Exit if typing is interrupted
        if (index < text.length) {
            textarea.value += text[index++];
            textarea.scrollTop = textarea.scrollHeight; // Scroll to bottom as text is typed
            setTimeout(typeText, typingSpeed);
        } else {
            smoothScrollToBottom(); // Ensure final scroll to bottom
        }
    }

    typeText();
}

// Add an event listener to the form for submitting
document.addEventListener('DOMContentLoaded', function () {
    const playbackButton = document.getElementById('playbackButton');
    const audio = document.getElementById('response-audio');

    // Add an event listener to the form for submitting
    document.getElementById('prompt-form').addEventListener('submit', function (e) {
        e.preventDefault();
        var prompt = document.getElementById('userInput').value; // Get text from the textarea
        sendRequest(prompt);
    });

    // Add an event listener to the playback button
    playbackButton.addEventListener('click', function () {
        if (audio.paused) {
            // Play audio if it is paused
            audio.play();
            playbackButton.textContent = '-¡!¡- Pause Audio -¡!¡-'; // Update button text to "Pause"
        } else {
            // Pause audio if it is playing
            audio.pause();
            playbackButton.textContent = '-¡!¡- PlayBack Audio -¡!¡-'; // Update button text to "Play"
        }
    });

    // Add an event listener to the audio element to reset button text when audio ends
    audio.addEventListener('ended', function () {
        playbackButton.textContent = '-¡!¡- PlayBack Audio -¡!¡-'; // Reset button text to "Play"
    });
});
