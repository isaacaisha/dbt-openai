document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const speechRecognitionButton = document.getElementById('speechRecognitionButton');
    const userInput = document.getElementById('writing_text');
    let userSpeechData = "";
    let recognition;

    // Check if webkitSpeechRecognition is supported
    if ('webkitSpeechRecognition' in window) {
        // Create a new webkitSpeechRecognition instance
        recognition = new webkitSpeechRecognition();

        // Event handler when speech recognition starts
        recognition.onstart = function () {
            speechRecognitionButton.textContent = 'Listening...';
        };

        // Event handler when speech recognition has a result
        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            userSpeechData = transcript;
            userInput.value = transcript;
            console.log(userSpeechData);
        };

        // Event handler when speech recognition ends
        recognition.onend = function () {
            speechRecognitionButton.textContent = 'Start Speech Recognition';
        // Show the textarea container
        const textareaContainer = document.getElementById('textarea-container');
        textareaContainer.style.display = 'block';
        };

        // Event handler for speech recognition errors
        recognition.onerror = function (event) {
            console.error('Speech recognition error:', event.error);
        };
    } else {
        // Disable the speech recognition button if not supported
        speechRecognitionButton.disabled = true;
        speechRecognitionButton.textContent = 'Speech Recognition Not Supported';
    }

    // Click event listener for speech recognition button
    speechRecognitionButton.addEventListener('click', function () {
        if (recognition && recognition.state === 'listening') {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

});
