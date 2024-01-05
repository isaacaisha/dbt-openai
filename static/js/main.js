// Disable all buttons with the class "btn" except language selection buttons
document.querySelectorAll('.btn:not(.language-btn, .submit)').forEach(function (btn) {
    btn.disabled = true;
});

// Add click event listeners to language buttons
var languageButtons = document.querySelectorAll('.language-btn');
languageButtons.forEach(function (button) {
    button.addEventListener('click', function () {
        // Remove the 'active' class from all buttons
        languageButtons.forEach(function (btn) {
            btn.classList.remove('active');
        });
        // Add the 'active' class to the clicked button
        button.classList.add('active');

        // Enable all buttons with the class "btn"
        document.querySelectorAll('.btn').forEach(function (btn) {
            btn.disabled = false;
        });
    });
});

document.getElementById('start-button').addEventListener('click', handleStartButtonClick);

let userTextData = ""; // Initialize a variable to store the text data
let typingTimeout; // Initialize a variable to track typing timeout

// Function to handle the "Start" button click
function handleStartButtonClick() {
    // Show the textarea container
    const textareaContainer = document.getElementById('textarea-container');
    textareaContainer.style.display = 'block';

    // Focus on the textarea
    const textarea = document.getElementById('writing_text');
    textarea.focus();

    // Listen for input in the textarea
    textarea.addEventListener('input', function () {
        // Clear any previous typing timeout
        clearTimeout(typingTimeout);

        // Set a new typing timeout
        typingTimeout = setTimeout(function () {
            // If the user hasn't typed for 19 seconds, clear the textarea
            textarea.value = "";
        }, 19000); // 19000 milliseconds (19 seconds)
    });
}

document.getElementById('conversationInterfaceForm').addEventListener('submit', function (event) {
    const writingText = document.getElementById('writing_text').value.trim();

    if (writingText === "") {
        // Display an error message if the writing text is empty
        document.getElementById('error-message').textContent =  "Please,\nYou Have To Speech or Enter Text\nFirst\n¡!¡ 😝 ¡!¡";
        document.getElementById('error-message').style.display = 'block';

        // Prevent the form from submitting when the writing text is empty
        event.preventDefault();
    } else {
        // Clear any previous error message
        document.getElementById('error-message').textContent = "";
        document.getElementById('error-message').style.display = 'none';

        // Add the sendRequest function here...
        var prompt = document.getElementById('writing_text').value; // Get text from the textarea
        sendRequest(prompt);
    }
});

function capitalizeSentences(textarea) {
    // Get the current value of the textarea
    let currentValue = textarea.value;

    // Split the text into sentences based on periods followed by a space
    let sentences = currentValue.split('. ');

    // Capitalize the first letter of each sentence and join them back together
    let capitalizedText = sentences.map(function (sentence) {
        return sentence.charAt(0).toUpperCase() + sentence.slice(1);
    }).join('. ');

    // Set the updated value
    textarea.value = capitalizedText;
}

// Add an event listener to the form for submitting
document.getElementById('prompt-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var prompt = document.getElementById('writing_text').value; // Get text from the textarea
    sendRequest(prompt);
});

// JavaScript function to toggle the visibility of the histories container
function toggleHistoriesJson() {
    var container = document.getElementById('historiesContainerJson');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}
