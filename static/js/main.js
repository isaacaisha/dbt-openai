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


// Function to handle audio playback
function initializeAudioPlayback() {
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
}


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
