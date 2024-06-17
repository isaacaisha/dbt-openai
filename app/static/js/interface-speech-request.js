// Function to send a POST request to the server
function sendRequest(prompt) {
    // Show loading indicator
    showLoading();

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/interface/answer', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            // Hide loading indicator
            hideLoading();

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
                audio.src = "data:audio/mp3;base64," + response.answer_audio;

                // Auto-play the audio when it's ready
                audio.oncanplay = function() {
                    audio.play();
                };
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

    function typeText() {
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
    document.getElementById('response-audio').onloadedmetadata = function () {
        this.play();
    };

    // Add an event listener to the playback button for audio
    document.getElementById('playAudioButton').addEventListener('click', function () {
        var audio = document.getElementById('response-audio');
        audio.play();
    });
});
