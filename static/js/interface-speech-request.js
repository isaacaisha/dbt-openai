// Function to send a POST request to the server
function sendRequest(prompt) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/interface/answer', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
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
                    speech.lang = activeLanguageButton.getAttribute('data-lang');
                } else {
                    speech.lang = 'en-EN'; // Default to English if no language is selected
                }

                // Add <lang> tags with the xml:lang attribute to switch languages
                speech.text = response.answer_text;

                window.speechSynthesis.speak(speech);
            } else {
                textarea.style.display = 'none';
            }

            // Set the audio source and play
            var audio = document.getElementById('response-audio');
            audio.src = "data:audio/mp3;base64," + response.answer_audio;

            // Auto-play the audio when it's ready
            audio.oncanplay = function() {
                audio.play();
            };
        }
    };
    xhr.send('prompt=' + encodeURIComponent(prompt));
}

// Add an event listener to the form for submitting
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('prompt-form').addEventListener('submit', function (e) {
        e.preventDefault();
        var prompt = document.getElementById('userInput').value; // Get text from the textarea
        sendRequest(prompt);
    });
});
