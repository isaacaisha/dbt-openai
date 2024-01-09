// Function to disable all buttons except language selection buttons
function disableButtons() {
    document.querySelectorAll('.btn:not(.language-btn, .submit)').forEach(btn => {
        btn.disabled = true;
    });
}

// Function to enable all buttons
function enableButtons() {
    document.querySelectorAll('.btn').forEach(btn => {
        btn.disabled = false;
    });
}

// Function to add click event listeners to language buttons
function addLanguageButtonClickListeners() {
    const languageButtons = document.querySelectorAll('.language-btn');
    languageButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Log button click for debugging
            console.log('Button clicked:', button);

            // Remove the 'active' class from all buttons
            languageButtons.forEach(btn => {
                btn.classList.remove('active');
                // Log the classList of each button for debugging
                console.log('Button classes after removal:', btn.classList);
            });

            // Add the 'active' class to the clicked button
            button.classList.add('active');
            // Enable all buttons with the class "btn"
            enableButtons();

            // Log the classList of the clicked button after adding 'active' class
            console.log('Button classes after adding "active":', button.classList);
        });
    });
}


// Function to capitalize sentences in a textarea
function capitalizeSentences(textarea) {
    let currentValue = textarea.value;
    let sentences = currentValue.split('. ');
    let capitalizedText = sentences.map(sentence => sentence.charAt(0).toUpperCase() + sentence.slice(1)).join('. ');
    textarea.value = capitalizedText;
}

// Function to handle the "Start" button click
function handleStartButtonClick() {
    const textareaContainer = document.getElementById('textarea-container');
    textareaContainer.style.display = 'block';
    const textarea = document.getElementById('writing_text');
    textarea.focus();
    textarea.addEventListener('input', function() {
        capitalizeSentences(textarea);
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(function() {
            textarea.value = "";
        }, 9000);
    });
}

// Function to handle speech recognition
function initializeSpeechRecognition() {
    const speechRecognitionButton = document.getElementById('speechRecognitionButton');
    const userInput = document.getElementById('writing_text');
    let userSpeechData = "";
    let recognition;

    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.onstart = function() {
            speechRecognitionButton.textContent = 'Listening...';
        };
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            userSpeechData = transcript;
            userInput.value = transcript;
            console.log('Speech data:', userSpeechData);
        };
        recognition.onend = function() {
            speechRecognitionButton.textContent = 'Start Speech Recognition';
        };
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
        };
    } else {
        speechRecognitionButton.disabled = true;
        speechRecognitionButton.textContent = 'Speech Recognition Not Supported';
    }

    speechRecognitionButton.addEventListener('click', function() {
        if (recognition && recognition.state === 'listening') {
            recognition.stop();
        } else {
            recognition.start();
        }
        const textareaContainer = document.getElementById('textarea-container');
        textareaContainer.style.display = 'block';
    });
}

// Function to send a POST request to the server
function sendRequest(prompt) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/conversation-interface', true);

    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
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
                        // Set voice explicitly by name
                        var selectedLang = activeLanguageButton.getAttribute('data-lang');
                        speech.voice = speechSynthesis.getVoices().find(voice => voice.lang === selectedLang);

                        // Add <lang> tags with the xml:lang attribute to switch languages
                        speech.lang = selectedLang;

                        // Set the text content for speech synthesis
                        speech.text = response.answer_text;
                    } else {

                        // Set the text content for speech synthesis
                        speech.text = response.answer_text;
                    }

                    console.log('Selected language:', speech.lang);

                    speech.onerror = function(event) {
                        console.error('Speech synthesis error:', event.error);
                    };

                    window.speechSynthesis.speak(speech);
                } else {
                    textarea.style.display = 'none';
                }

                // Set the audio source and play
                var audio = document.getElementById('response-audio');
                audio.src = "data:audio/mp3;base64," + response.answer_audio;
                audio.style.display = 'block';

                // Auto-play the audio when it's ready
                audio.oncanplay = function () {
                    audio.play();
                };

                // Clear any previous error message
                var errorMessage = document.getElementById('error-message');
                errorMessage.innerText = '';
                errorMessage.style.display = 'none';
            } else if (xhr.status === 401) {
                // User is not authenticated, display the error message
                var errorMessage = document.getElementById('error-message');
                errorMessage.innerText = 'You must be logged in\nto use this feature.\nPlease register and log in.\nOr reload the page, thanks\n¡!¡ 😇 ¡!¡';
                errorMessage.style.display = 'block';
            } else {
                // Handle other HTTP error statuses if needed
                console.error('HTTP error! Status:', xhr.status);
            }
        }
    };

    var requestBody = 'prompt=' + encodeURIComponent(prompt);
    xhr.send(requestBody);
}


// The rest of your code (audio playback, toggleHistoriesJson, etc.) goes here...
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById('response-audio').onloadedmetadata = function () {
        this.play();
    };

    document.getElementById('playAudioButton').addEventListener('click', function () {
        var audio = document.getElementById('response-audio');
        audio.play();
    });
});


// Function to toggle histories JSON container
function toggleHistoriesJson() {
    var container = document.getElementById('historiesContainerJson');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}

// Main entry point
document.addEventListener('DOMContentLoaded', function() {
    disableButtons();
    addLanguageButtonClickListeners();
    initializeSpeechRecognition();
    initializeAudioPlayback();
    // ... (add other initialization logic)

    document.getElementById('start-button').addEventListener('click', handleStartButtonClick);

    document.getElementById('conversationInterfaceForm').addEventListener('submit', function(event) {
        const writingText = document.getElementById('writing_text').value.trim();
        if (writingText === "") {
            document.getElementById('error-message').textContent = "Please, You Have To Speech or Enter Text First ¡!¡ 😝 ¡!¡";
            document.getElementById('error-message').style.display = 'block';
            event.preventDefault();
        } else {
            document.getElementById('error-message').textContent = "";
            document.getElementById('error-message').style.display = 'none';
            const formData = new FormData(document.getElementById('conversationInterfaceForm'));
            sendRequest(formData);
        }
    });
});
