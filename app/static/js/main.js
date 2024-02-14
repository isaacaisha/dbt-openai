// Disable all buttons with the class "btn" except language selection buttons
document.querySelectorAll('.btn:not(.language-btn, .submit)').forEach(function (btn) {
    btn.disabled = true;
});

// Function to enable content when a language is selected
function enableContent() {
    // Show the content container
    document.getElementById('content-container').style.display = 'block';

    // Enable all buttons with the class "btn"
    document.querySelectorAll('.btn').forEach(function (btn) {
        btn.disabled = false;
    });
}

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

        // Call the enableContent function to show the content container and enable all buttons
        enableContent();
    });
});

// Function to capitalize sentences in a textarea
function capitalizeSentences(textarea) {
    // Get the current value of the textarea
    let currentValue = textarea.value;

    // Split the text into sentences based on periods followed by a space
    let sentences = currentValue.split('. ');

    // Capitalize the first letter of each sentence and join them back together
    let capitalizedText = sentences.map(sentence => {
        return sentence.charAt(0).toUpperCase() + sentence.slice(1);
    }).join('. ');

    // Set the updated value
    textarea.value = capitalizedText;
}

// Initialize variables to store text data and track typing timeout
let userTextData = "";
let typingTimeout;

// Function to handle the "Start" button click
document.getElementById('start-button').addEventListener('click', function () {
    // Show the textarea container
    const textareaContainer = document.getElementById('textarea-container');
    textareaContainer.style.display = 'block';

    // Focus on the textarea
    const textarea = document.getElementById('userInput');
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
});

// Function to handle the "Generate" button click
document.getElementById('generateButton').addEventListener('click', function (event) {
    const speechData = userSpeechData.trim(); // Get the trimmed speech data
    const inputText = userInput.value.trim(); // Get the trimmed input text

    if (speechData === "" && inputText === "") {
        // Display an error message if both fields are empty
        document.getElementById('error-message').textContent = "Please, You Have To Speech or Enter Text First 😝";

        // Show the error message
        document.getElementById('error-message').style.display = 'block';

        // Prevent the form from submitting when both fields are empty
        event.preventDefault();
    } else {
        // Clear any previous error message
        document.getElementById('error-message').textContent = "";

        // Hide the error message
        document.getElementById('error-message').style.display = 'none';
    }
});

// Listen for input in the textarea and store the text
document.getElementById('userInput').addEventListener('input', function () {
    userTextData = document.getElementById('userInput').value;
});
