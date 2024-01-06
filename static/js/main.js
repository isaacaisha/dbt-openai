document.addEventListener('DOMContentLoaded', function () {
    const speechRecognitionButton = document.getElementById('speechRecognitionButton');
    const userInput = document.getElementById('writing_text');
    let userSpeechData = "";
    let recognition;

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
            document.getElementById('error-message').textContent = "Please,\nYou Have To Speech or Enter Text\nFirst\n¡!¡ 😝 ¡!¡";
            document.getElementById('error-message').style.display = 'block';

            event.preventDefault();
        } else {
            document.getElementById('error-message').textContent = "";
            document.getElementById('error-message').style.display = 'none';

            const formData = new FormData(document.getElementById('conversationInterfaceForm'));
            formData.append('writing_text', writingText);

            sendRequest(formData);
        }
    });

    function capitalizeSentences(textarea) {
        let currentValue = textarea.value;
        let sentences = currentValue.split('. ');
        let capitalizedText = sentences.map(function (sentence) {
            return sentence.charAt(0).toUpperCase() + sentence.slice(1);
        }).join('. ');

        textarea.value = capitalizedText;
    }

    document.getElementById('prompt-form').addEventListener('submit', function (e) {
        e.preventDefault();
        var prompt = document.getElementById('writing_text').value;
        sendRequest(prompt);
    });

    const API_ENDPOINT = '/conversation-interface';
    const CONTENT_TYPE = 'application/x-www-form-urlencoded';
    const DEFAULT_LANGUAGE = 'en-US';

    function sendRequest(formData) {
        const activeLanguageButton = document.querySelector('.language-btn.active');
        const selectedLanguage = activeLanguageButton ? activeLanguageButton.getAttribute('data-lang') : DEFAULT_LANGUAGE;
        formData.append('language', selectedLanguage);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', API_ENDPOINT, true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                handleResponse(xhr);
            }
        };
        xhr.send(formData);
    }

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

    function handleSuccess(response) {
        const textarea = document.getElementById('generatedText');
        textarea.value = response.answer_text;

        if (response.answer_text) {
            textarea.style.display = 'block';

            const speech = new SpeechSynthesisUtterance(response.answer_text);
            const activeLanguageButton = document.querySelector('.language-btn.active');

            speech.lang = activeLanguageButton ? activeLanguageButton.getAttribute('data-lang') : DEFAULT_LANGUAGE;

            const voices = window.speechSynthesis.getVoices();
            const selectedVoice = voices.find(voice => voice.lang === speech.lang);
            speech.voice = selectedVoice;

            window.speechSynthesis.speak(speech);
        } else {
            textarea.style.display = 'none';
        }

        const audio = document.getElementById('response-audio');
        audio.src = "data:audio/mp3;base64," + response.answer_audio;
        audio.style.display = 'block';

        audio.onloadedmetadata = function () {
            audio.play();
        };

        const errorMessage = document.getElementById('error-message');
        errorMessage.innerText = '';
        errorMessage.style.display = 'none';
    }

    function handleAuthenticationError() {
        const errorMessage = document.getElementById('error-message');
        errorMessage.innerText = 'You must be logged in\nto use this feature.\nPlease register and log in.\n¡!¡ 😇 ¡!¡';
        errorMessage.style.display = 'block';
    }

    function handleOtherError(status) {
        console.error('HTTP error! Status:', status);
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.getElementById('response-audio').onloadedmetadata = function () {
            this.play();
        };

        document.getElementById('playAudioButton').addEventListener('click', function () {
            var audio = document.getElementById('response-audio');
            audio.play();
        });
    });
});

function toggleHistoriesJson() {
    var container = document.getElementById('historiesContainerJson');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}