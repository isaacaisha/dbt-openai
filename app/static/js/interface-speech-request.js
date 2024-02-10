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

                // Toggle visibility of the textarea based on response
                if (response.answer_text) {
                    textarea.style.display = 'block';

                    // Use the SpeechSynthesis API to read the response aloud
                    var speech = new SpeechSynthesisUtterance(response.answer_text);

                    // Get the active language button and set speech.lang based on its data-lang attribute
                    var activeLanguageButton = document.querySelector('.language-btn.active');
                    if (activeLanguageButton) {
                        speech.lang = activeLanguageButton.getAttribute('data-lang');
                    } else {
                        speech.lang = 'es-ES'; // Default to Spanish if no language is selected
                    }

                    // Add <lang> tags with the xml:lang attribute to switch languages
                    speech.text = response.answer_text;

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
            } else if (xhr.status === 401) {
                // Handle 401 Unauthorized status
                var errorContainer = document.getElementById('error-message');
                errorContainer.textContent =
                    "-¡!¡- RE-CLICK Or LOGIN -¡!¡-";
                errorContainer.style.display = 'block';
            } else {
                // Handle other HTTP status codes
                var errorContainer = document.getElementById('error-message');
                errorContainer.textContent =
                    "-¡!¡- RE-CLICK Or LOGIN -¡!¡-";
                errorContainer.style.display = 'block';
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

        // Get the active language button and set speech.lang based on its data-lang attribute
        var activeLanguageButton = document.querySelector('.language-btn.active');
        if (activeLanguageButton) {
            speech.lang = activeLanguageButton.getAttribute('data-lang');
        } else {
            speech.lang = 'es-ES'; // Default to Spanish if no language is selected
        }

        // Add <lang> tags with the xml:lang attribute to switch languages
        speech.text = document.getElementById('generatedText').value;

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
