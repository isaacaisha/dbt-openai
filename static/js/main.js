// Other functions (capitalizeSentences, sendRequest, handleResponse, handleSuccess, etc.) go here...

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

function toggleHistoriesJson() {
    var container = document.getElementById('historiesContainerJson');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}


document.addEventListener('DOMContentLoaded', function () {
    const speechRecognitionButton = document.getElementById('speechRecognitionButton');
    const userInput = document.getElementById('writing_text');
    let userSpeechData = "";
    let recognition;

    // Language configuration
    let selectedLanguage = 'en-US'; // Default language

    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.onerror = function (event) {
            console.error('Speech recognition error:', event.error);
        };

        recognition.onstart = function () {
            speechRecognitionButton.textContent = 'Listening...';
        };

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            userSpeechData = transcript;
            userInput.value = transcript;
            console.log(userSpeechData);
        };

        recognition.onend = function () {
            speechRecognitionButton.textContent = 'Start Speech Recognition';
        };

    } else {
        speechRecognitionButton.disabled = true;
        speechRecognitionButton.textContent = 'Speech Recognition Not Supported';
    }

    speechRecognitionButton.addEventListener('click', function () {
        if (recognition && recognition.state === 'listening') {
            recognition.stop();
        } else {
            recognition.start();
        }

        const textareaContainer = document.getElementById('textarea-container');
        textareaContainer.style.display = 'block';
    });

    document.getElementById('start-button').addEventListener('click', handleStartButtonClick);

    function handleStartButtonClick() {
        let typingTimeout;
        const textareaContainer = document.getElementById('textarea-container');
        textareaContainer.style.display = 'block';

        const textarea = document.getElementById('writing_text');
        textarea.focus();

        capitalizeSentences(textarea);

        textarea.addEventListener('input', function () {
            clearTimeout(typingTimeout);

            typingTimeout = setTimeout(function () {
                textarea.value = "";
            }, 19000);
        });
    }

    document.getElementById('conversationInterfaceForm').addEventListener('submit', function (event) {
        const writingText = document.getElementById('writing_text').value.trim();

        if (writingText === "") {
            document.getElementById('error-message').textContent = "Please,\nYou Have To Speech or\nEnter Text First\n¡!¡ 😝 ¡!¡";
            document.getElementById('error-message').style.display = 'block';

            event.preventDefault();
        } else {
            document.getElementById('error-message').textContent = "";
            document.getElementById('error-message').style.display = 'none';

            const formData = new FormData(document.getElementById('conversationInterfaceForm'));
            formData.append('language', selectedLanguage);

            sendRequest(formData);
        }
    });

});
