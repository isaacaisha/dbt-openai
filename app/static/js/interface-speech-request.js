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
    showLoading();
    const buttons = ['speechRecognitionButton', 'generateButton', 'playbackButton', 'start-button'];
    buttons.forEach(id => document.getElementById(id).disabled = true);
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
                const textarea = document.getElementById('generatedText');
                textarea.value = response.answer_text;
                textarea.dataset.detectedLang = response.detected_lang || 'es-ES';
                textarea.style.display = response.answer_text ? 'block' : 'none';
                document.getElementById('response-audio').style.display = 'block';
                document.getElementById('playbackButtonContainer').style.display = 'block';

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
            } else {
                interruptButton.style.display = 'none';
                console.error('Request failed:', xhr.status, xhr.statusText);
            }
        }
    };

    xhr.onerror = function () {
        hideLoading();
        buttons.forEach(id => document.getElementById(id).disabled = false);
        disableAllButtons(false);
        console.error('Network error');
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
                audio.load();
            }
        }
    };

    xhr.send();
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
    loadingIndicator.style.display = 'block';
}

// Function to hide the loading indicator
function hideLoading() {
    const loadingIndicator = document.getElementById('loading-indicator');
    loadingIndicator.style.display = 'none';
}

// Function to smoothly scroll the textarea to the bottom
function smoothScrollToBottom() {
    const textarea = document.getElementById('generatedText');
    const start = textarea.scrollTop;
    const end = textarea.scrollHeight;
    const change = end - start;
    const duration = 1000; // Duration for scrolling
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
    textarea.value = ''; // Clear the textarea before typing starts
    let index = 0;
    const typingSpeed = 57; // Adjust this value to control typing speed
    let typingInProgress = true; // Set the typing flag to true

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

// Add event listeners on DOMContentLoaded
document.addEventListener('DOMContentLoaded', function () {
    const playbackButton = document.getElementById('playbackButton');
    const audio = document.getElementById('response-audio');

    // Add event listener to form submit
    document.getElementById('prompt-form').addEventListener('submit', function (e) {
        e.preventDefault();
        const prompt = document.getElementById('userInput').value; // Get text from the textarea
        sendRequest(prompt);
    });

    // Add event listener to playback button
    playbackButton.addEventListener('click', function () {
        if (audio.paused) {
            audio.play();
            playbackButton.textContent = '-¡!¡- Pause Audio -¡!¡-';
        } else {
            audio.pause();
            playbackButton.textContent = '-¡!¡- PlayBack Audio -¡!¡-';
        }
    });

    // Add event listener to reset button text when audio ends
    audio.addEventListener('ended', function () {
        playbackButton.textContent = '-¡!¡- PlayBack Audio -¡!¡-';
    });
});
