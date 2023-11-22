// Disable all buttons with the class "btn" except language selection buttons
document.querySelectorAll('.btn:not(.language-btn)').forEach(function(btn) {
    btn.disabled = true;
});

// Add click event listeners to language buttons
var languageButtons = document.querySelectorAll('.language-btn');
languageButtons.forEach(function(button) {
    button.addEventListener('click', function() {
        // Remove the 'active' class from all buttons
        languageButtons.forEach(function(btn) {
            btn.classList.remove('active');
        });
        // Add the 'active' class to the clicked button
        button.classList.add('active');

        // Enable all buttons with the class "btn"
        document.querySelectorAll('.btn').forEach(function(btn) {
            btn.disabled = false;
        });
    });
});

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

let userTextData = ""; // Initialize a variable to store the text data
let typingTimeout; // Initialize a variable to track typing timeout

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

document.getElementById('generateButton').addEventListener('click', function (event) {
    const speechData = userTextData.trim(); // Get the trimmed speech data
    const inputText = userInput.value.trim(); // Get the trimmed input text

    if (speechData === "" && inputText === "") {
        // Display an error message if both fields are empty
        document.getElementById('error-message').textContent = "Please,\nYou Have To Speech or Enter Text\nFirst 😝";
        document.getElementById('error-message').style.display = 'block';

        // Hide the "Final Result" content since there's no recognized speech or input text
        document.getElementById('final-result-speech-content').style.display = 'none';

        // Prevent the form from submitting when both fields are empty
        event.preventDefault();
    } else {
        // Clear any previous error message
        document.getElementById('error-message').textContent = "";
        document.getElementById('error-message').style.display = 'none';

        // Display the content in the "Final Result" section
        document.getElementById('final-result-content').textContent = userTextData;
        document.getElementById('final-result-content').style.display = 'block';
    }
});

// Add a click event listener to the "Final Result" button
document.getElementById('final_result').addEventListener('click', function () {
    // Check if the textarea is empty
    if (userTextData.trim() === "") {
        // Display an error message
        document.getElementById('error-message').textContent = "Please,\nYou Have To Write\nFirst 😝";
        document.getElementById('error-message').style.display = 'block';

        // Hide the "Final Result" content since there's no text
        document.getElementById('final-result-content').style.display = 'none';
    } else {
        // Clear any previous error message
        document.getElementById('error-message').textContent = "";
        document.getElementById('error-message').style.display = 'none';

        // Display the content in the "Final Result" section
        document.getElementById('final-result-content').textContent = userTextData;
        document.getElementById('final-result-content').style.display = 'block';
    }
});

// Listen for input in the textarea and store the text
document.getElementById('userInput').addEventListener('input', function () {
    userTextData = document.getElementById('userInput').value;
});

// Initially, hide the "Final Result" content and error message
document.getElementById('final-result-content').style.display = 'none';
document.getElementById('error-message').style.display = 'none';



// JavaScript to toggle the visibility of the memory-load btn
function toggleResultMemo() {
    var resultDiv = document.getElementById("resultMemo");
    var memoryTextarea = document.getElementById("memoryTextarea");

    if (memoryTextarea.value.trim() !== "") {
        if (resultDiv.style.display === "none" || resultDiv.style.display === "") {
            resultDiv.style.display = "block";
        } else {
            resultDiv.style.display = "none";
        }

        // Set the line height for the text area (adjust the value as needed)
        memoryTextarea.style.lineHeight = "1.9"; // Adjust the line height as needed
    }
}

// Add a click event listener to the "Show History" button
document.getElementById('showResultButton').addEventListener('click', function () {
    var memoryTextarea = document.getElementById("memoryTextarea");
    var resultDiv = document.getElementById("resultMemo"); // Define resultDiv here

    if (memoryTextarea.value.trim() === "") {
        // Display an error message
        document.getElementById('error-message').textContent = "Please,\nConverse with the App First,\nThen Reload the Page\n 😝";
        document.getElementById('error-message').style.display = 'block';
        resultDiv.style.display = 'none';
    } else {
        // Display the content in the "Final Result" section
        document.getElementById('error-message').textContent = "";
        document.getElementById('error-message').style.display = 'none';

        document.getElementById('textarea-memory').textContent = memoryTextarea.value;
        document.getElementById('textarea-memory').style.display = 'block';
        resultDiv.style.display = 'block';
    }
});

// Add click event listener to the "Conversation Details" button
document.getElementById('conversation-details').addEventListener('click', function (event) {
    // Check if there's no text entered and no speech data
    const speechData = userTextData.trim(); // Get the trimmed speech data
    const inputText = userInput.value.trim(); // Get the trimmed input text

    if (speechData === "" && inputText === "") {
        // Display an error message
        document.getElementById('error-message').textContent = "Please,\nInteract with the App\nFirst 😝";
        document.getElementById('error-message').style.display = 'block';

        // Prevent the default behavior of the anchor link
        event.preventDefault();
    }
});
