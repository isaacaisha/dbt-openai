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

// Function to show the loading indicator
function showLoading() {
    const loadingIndicator = document.getElementById('loading-indicator');
    const loadingCircle = document.getElementById('loading-circle');
    loadingIndicator.style.display = 'block';
    loadingCircle.style.display = 'block';
}

// Function to hide the loading indicator
function hideLoading() {
    const loadingIndicator = document.getElementById('loading-indicator');
    const loadingCircle = document.getElementById('loading-circle');
    loadingIndicator.style.display = 'none';
    loadingCircle.style.display = 'none';
}

// Function to handle errors in the XMLHttpRequest
function handleRequestError() {
    hideLoading();
    disableAllButtons(false);
    console.error('Network or request error occurred');
}

// Function to process the response from the server
function processResponse(responseText) {
    const response = JSON.parse(responseText);
    const textarea = document.getElementById('generatedText');
    textarea.value = response.answer_text;
    textarea.dataset.detectedLang = response.detected_lang || 'es-ES';
    textarea.style.display = response.answer_text ? 'block' : 'none';
    document.getElementById('response-audio').style.display = 'block';
    document.getElementById('playbackButtonContainer').style.display = 'block';

    if (response.flash_message) {
        document.getElementById('flash-message').textContent = response.flash_message;
    }

    if (response.answer_text) {
        smoothScrollToBottomWhileTyping(response.answer_text);
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
    updateAudioSource();
    interruptButton.style.display = 'block';
}

// Function to send a POST request to the server
function sendRequest(prompt) {
    const csrfToken = getCookie('csrf_token');
    showLoading();
    disableAllButtons(true);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/interface/answer', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.setRequestHeader('X-CSRFToken', csrfToken);

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            hideLoading();
            disableAllButtons(false);

            if (xhr.status === 200) {
                processResponse(xhr.responseText);
            } else {
                handleRequestError();
            }
        }
    };

    xhr.onerror = handleRequestError;

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
                audio.load();
            }
        }
    };

    xhr.send();
}

// Function to smoothly scroll the textarea to the bottom
function smoothScrollToBottom() {
    const textarea = document.getElementById('generatedText');
    const start = textarea.scrollTop;
    const end = textarea.scrollHeight;
    const change = end - start;
    const duration = 1000;
    const startTime = performance.now();

    function scroll(timestamp) {
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        textarea.scrollTop = start + (change * progress);
        if (progress < 1) {
            requestAnimationFrame(scroll);
        }
    }

    requestAnimationFrame(scroll);
}

// Function to scroll gradually while text is being typed
function smoothScrollToBottomWhileTyping(text) {
    const textarea = document.getElementById('generatedText');
    textarea.value = '';
    let index = 0;
    const typingSpeed = 57;
    let typingInProgress = true;

    function typeText() {
        if (!typingInProgress) return;
        if (index < text.length) {
            textarea.value += text[index++];
            textarea.scrollTop = textarea.scrollHeight;
            setTimeout(typeText, typingSpeed);
        } else {
            smoothScrollToBottom();
        }
    }

    typeText();
}

// Add event listeners when the document is ready
document.addEventListener('DOMContentLoaded', function () {
    const audio = document.getElementById('response-audio');

    document.getElementById('prompt-form').addEventListener('submit', function (e) {
        e.preventDefault();
        const prompt = document.getElementById('userInput').value;
        sendRequest(prompt);
    });

    document.getElementById('playbackButton').addEventListener('click', function () {
        const playbackButton = document.getElementById('playbackButton');

        if (audio.paused) {
            audio.play();
            playbackButton.textContent = '-¡!¡- Pause Audio -¡!¡-';
        } else {
            audio.pause();
            playbackButton.textContent = '-¡!¡- PlayBack Audio -¡!¡-';
        }
    });

    audio.addEventListener('click', function () {
        audio.play();
    });
});
