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

    // Disable the "Get The Response" button and "PlayBack" button
    var speechRecognitionButton = document.getElementById('speechRecognitionButton');
    var generateButton = document.getElementById('generateButton');
    var playbackButton = document.getElementById('playbackButton');
    speechRecognitionButton.disabled = true;
    generateButton.disabled = true;
    playbackButton.disabled = true;

    xhr = new XMLHttpRequest(); // Use the global xhr variable
    xhr.open('POST', '/home/answer', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.setRequestHeader('X-CSRFToken', csrfToken);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            // Hide loading indicator
            hideLoading();

            // Re-enable the "Get The Response" button and "PlayBack" button
            speechRecognitionButton.disabled = false;
            generateButton.disabled = false;
            playbackButton.disabled = false;

            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);

                // Display the text response in the textarea
                var textarea = document.getElementById('generatedText');
                textarea.value = response.answer_text;

                // Store the detected language as a data attribute
                textarea.dataset.detectedLang = response.detected_lang || 'es-ES';

                // Toggle visibility of the textarea based on response
                if (response.answer_text) {
                    textarea.style.display = 'block';

                    // Scroll to the bottom of the container while text is being added
                    smoothScrollToBottomWhileTyping(response.answer_text);

                    // Use the SpeechSynthesis API to read the response aloud
                    var speech = new SpeechSynthesisUtterance(response.answer_text);

                    // Use the detected language from the response
                    speech.lang = response.detected_lang || 'es-ES';

                    // Hide the interrupt button when speech ends
                    speech.onend = function () {
                        interruptButton.style.display = 'none';
                    };

                    // Scroll as the speech is being spoken
                    speech.onboundary = function (event) {
                        if (event.name === 'word') {
                            smoothScrollToBottom();
                        }
                    };

                    window.speechSynthesis.speak(speech);
                } else {
                    textarea.style.display = 'none';
                }

                // Set the audio source and play
                var audio = document.getElementById('response-audio');
                //audio.src = "data:audio/mp3;base64," + response.answer_audio;
                audio.src = response.answer_audio_path;
                audio.style.display = 'block';
                playbackButton.classList.remove('hidden');

                // // Auto-play the audio when it's ready
                // audio.oncanplay = function() {
                //     audio.play();
                // };

                // Ensure the stop button remains visible during speech synthesis
                interruptButton.style.display = 'block';
            } else {
                interruptButton.style.display = 'none'; // Hide the interrupt button if request fails
            }
        }
    };
    xhr.send('prompt=' + encodeURIComponent(prompt));
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
    document.getElementById('prompt-form').addEventListener('submit', function (e) {
        e.preventDefault();
        var prompt = document.getElementById('userInput').value; // Get text from the textarea
        sendRequest(prompt);
    });

    // Add an event listener to the playback button
    document.getElementById('playbackButton').addEventListener('click', function () {
        // Use the SpeechSynthesis API to read the response aloud
        var speech = new SpeechSynthesisUtterance(document.getElementById('generatedText').value);

        // Use the detected language from the response
        var detectedLang = document.getElementById('generatedText').dataset.detectedLang;
        speech.lang = detectedLang || 'es-ES'; // Use detected language

        window.speechSynthesis.speak(speech);
    });

    // Add an event listener to the audio element for playback
    document.getElementById('response-audio').addEventListener('click', function () {
        var audio = document.getElementById('response-audio');
        audio.play();
    });
});
