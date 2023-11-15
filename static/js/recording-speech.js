document.addEventListener('DOMContentLoaded', function() {
    const speechRecognitionButton = document.getElementById('speechRecognitionButton');
    const userInput = document.getElementById('userInput');
    let userSpeechData = "";
    let recognition;

    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();

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

        recognition.onerror = function (event) {
            console.error('Speech recognition error:', event.error);
        };
    } else {
        speechRecognitionButton.disabled = true;
        speechRecognitionButton.textContent = 'Speech Recognition Not Supported';
    }

    // Click event listener for speech recognition
    speechRecognitionButton.addEventListener('click', function () {
        if (recognition && recognition.state === 'listening') {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    // Click event listener for the "Final Result" button
    document.getElementById('final_result_speech').addEventListener('click', function () {
        if (userSpeechData.trim() === "") {
            document.getElementById('error-message').textContent = "Please,\nYou Have To Speech\nFirst 😝";
            document.getElementById('error-message').style.display = 'block';
            document.getElementById('final-result-speech-content').style.display = 'none';
        } else {
            document.getElementById('error-message').textContent = "";
            document.getElementById('error-message').style.display = 'none';
            document.getElementById('final-result-speech-content').textContent = userSpeechData;
            document.getElementById('final-result-speech-content').style.display = 'block';
        }
    });
});
