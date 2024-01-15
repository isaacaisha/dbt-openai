const speechRecognitionButton = document.getElementById('speechRecognitionButton');
const userInput = document.getElementById('userInput');
// Initialize variables
let userSpeechData = ""; // Initialize a variable to store the speech data
let recognition;

// Check if speech recognition is supported in the browser
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();

    recognition.onstart = function () {
        // Speech recognition started
        speechRecognitionButton.textContent = 'Listening...';
    };

    recognition.onresult = function (event) {
        // Speech recognition result
        const transcript = event.results[0][0].transcript;
        userSpeechData = transcript; // Update userSpeechData
        userInput.value = transcript; // Update the userInput element

        // Print the speech content to the console
        console.log(userSpeechData);
    };

    recognition.onend = function () {
        // Speech recognition ended
        speechRecognitionButton.textContent = 'Start Speech Recognition';
    };

    recognition.onerror = function (event) {
        // Speech recognition error
        console.error('Speech recognition error:', event.error);
    };
} else {
    // Speech recognition not supported in this browser
    speechRecognitionButton.disabled = true;
    speechRecognitionButton.textContent = 'Speech Recognition Not Supported';
}

// Add a click event listener to start or stop speech recognition
speechRecognitionButton.addEventListener('click', function () {
    if (recognition && recognition.state === 'listening') {
        // If recognition is already running, stop it
        recognition.stop();
    } else {
        // If recognition is not running, start it
        recognition.start();
    }
    // Show the textarea container
    const textareaContainer = document.getElementById('textarea-container');
    textareaContainer.style.display = 'block';
});
