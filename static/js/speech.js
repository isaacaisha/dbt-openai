// Function to send a POST request to the server
function sendRequest(prompt) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/conversation-interface', true);

    // Set request headers, including the CSRF token
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    }

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            console.log(xhr.status);
            if (xhr.status === 200) {
                console.log(xhr.responseText);
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
                        speech.lang = 'en-US'; // Default to English if no language is selected
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
                errorMessage.innerText = 'You must be logged in\nto use this feature.\nPlease register and log in.\n¡!¡ 😇 ¡!¡';
                errorMessage.style.display = 'block';
            } else {
                // Handle other HTTP error statuses if needed
                console.error('HTTP error! Status:', xhr.status);
            }
        }
    };

    // Include the CSRF token in the request body
    var requestBody = 'writing_text=' + encodeURIComponent(prompt);
    }
    xhr.send(requestBody);
}
