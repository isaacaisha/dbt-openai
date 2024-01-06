// Constants
const API_ENDPOINT = '/conversation-interface';
const CONTENT_TYPE = 'application/x-www-form-urlencoded';
const DEFAULT_LANGUAGE = 'en-US';

// Function to send a POST request to the server
function sendRequest(prompt) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', API_ENDPOINT, true);
    xhr.setRequestHeader('Content-Type', CONTENT_TYPE);

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            handleResponse(xhr);
        }
    };

    // Include the CSRF token in the request body
    const requestBody = 'writing_text=' + encodeURIComponent(prompt);
    xhr.send(requestBody);
}

// Function to handle the server response
function handleResponse(xhr) {
    console.log(xhr.status);
    if (xhr.status === 200) {
        console.log(xhr.responseText);
        const response = JSON.parse(xhr.responseText);
        handleSuccess(response);
    } else if (xhr.status === 401) {
        handleAuthenticationError();
    } else {
        handleOtherError(xhr.status);
    }
}

// Function to handle successful response
function handleSuccess(response) {
    const textarea = document.getElementById('generatedText');
    textarea.value = response.answer_text;

    // Toggle visibility of the textarea based on response
    if (response.answer_text) {
        textarea.style.display = 'block';

        // Use the SpeechSynthesis API to read the response aloud
        const speech = new SpeechSynthesisUtterance(response.answer_text);
        const activeLanguageButton = document.querySelector('.language-btn.active');

        speech.lang = activeLanguageButton ? activeLanguageButton.getAttribute('data-lang') : DEFAULT_LANGUAGE;
        speech.text = response.answer_text;

        window.speechSynthesis.speak(speech);
    } else {
        textarea.style.display = 'none';
    }

    const audio = document.getElementById('response-audio');
    audio.src = "data:audio/mp3;base64," + response.answer_audio;
    audio.style.display = 'block';

    // Auto-play the audio when it's ready
    audio.onloadedmetadata = function () {
        audio.play();
    };

    // Clear any previous error message
    const errorMessage = document.getElementById('error-message');
    errorMessage.innerText = '';
    errorMessage.style.display = 'none';
}

// Function to handle authentication error
function handleAuthenticationError() {
    const errorMessage = document.getElementById('error-message');
    errorMessage.innerText = 'You must be logged in\nto use this feature.\nPlease register and log in.\n¡!¡ 😇 ¡!¡';
    errorMessage.style.display = 'block';
}

// Function to handle other HTTP errors
function handleOtherError(status) {
    console.error('HTTP error! Status:', status);
}

// Send a request with an empty prompt to trigger the response on page load
document.addEventListener("DOMContentLoaded", function () {
    sendRequest(requestBody);
    // Auto-play the audio when it's ready
    document.getElementById('response-audio').onloadedmetadata = function () {
        this.play();
    };

    // Add click event listener to the Play Audio button
    document.getElementById('playAudioButton').addEventListener('click', function () {
        var audio = document.getElementById('response-audio');
        audio.play();
    });
});
