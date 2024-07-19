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
    const buttons = ['speechRecognitionButton', 'generateButton', 'start-button'];
    buttons.forEach(id => document.getElementById(id).disabled = true);

    // Disable all buttons except navigation buttons
    disableAllButtons(true);
    interruptButton.disabled = false;

    const xhr = new XMLHttpRequest(); // Use local variable
    xhr.open('POST', '/interface/answer', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.setRequestHeader('X-CSRFToken', csrfToken);

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            // Hide loading indicator
            hideLoading();

            // Re-enable buttons
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

                // Toggle visibility of the textarea based on response
                if (response.answer_text)

                    // Scroll to the bottom of the container while text is being added
                    smoothScrollToBottomWhileTyping(response.answer_text);

                    // Use the SpeechSynthesis API to read the response aloud
                    const speech = new SpeechSynthesisUtterance(response.answer_text);

                    // Use the detected language from the response
                    speech.lang = response.detected_lang || 'es-ES';

                    // Hide the interrupt button when speech ends
                    speech.onend = () => interruptButton.style.display = 'none';

                    // Scroll as the speech is being spoken
                    speech.onboundary = function (event) {
                        speech.onboundary = event => {
                            if (event.name === 'word') {
                                smoothScrollToBottom();
                            }
                    };
                    window.speechSynthesis.speak(speech);
                } 

                // Set the audio source and play
                const audio = document.getElementById('response-audio');
                const playback = document.getElementById('playbackButton');
                //audio.src = response.answer_audio_path;
                audio.src = '/media/interface_temp_audio.mp3';
                audio.style.display = 'block';
                playback.style.display = 'block';

                // Auto-play the audio when it's ready
                audio.oncanplay = function() {
                    audio.play();
                };


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
